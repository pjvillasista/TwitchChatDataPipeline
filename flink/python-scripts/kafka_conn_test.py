from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import time

def create_kafka_source(t_env):
    chat_source_ddl = """
    CREATE TABLE chat_messages (
        stream_id STRING,
        subscription_id STRING,
        subscription_type STRING, 
        message_id STRING,
        broadcaster_user_id STRING,
        broadcaster_user_name STRING,
        broadcaster_user_login STRING,
        chatter_user_id STRING,
        chatter_user_name STRING,
        chatter_user_login STRING,
        message_text STRING,
        message_type STRING,
        badges ARRAY<ROW<set_id STRING, id STRING, info STRING>>,
        `timestamp` STRING
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'chat_messages',
        'properties.bootstrap.servers' = 'kafka:9092',
        'properties.group.id' = 'flink-consumer',
        'scan.startup.mode' = 'earliest-offset',
        'format' = 'avro-confluent',
        'avro-confluent.schema-registry.url' = 'http://schema-registry:8081'
    )
    """
    t_env.execute_sql(chat_source_ddl)

def create_iceberg_catalog(t_env):
    config = t_env.get_config().get_configuration()
    config.set_string("execution.checkpointing.interval", "10s")
    config.set_string("state.backend", "filesystem")
    config.set_string("state.checkpoints.dir", "s3://warehouse/flink-checkpoints")
    
    catalog_ddl = """
    CREATE CATALOG iceberg_catalog WITH (
        'type'='iceberg',
        'catalog-impl'='org.apache.iceberg.rest.RESTCatalog',
        'uri'='http://rest:8181',
        'warehouse'='s3://warehouse',
        'io-impl'='org.apache.iceberg.aws.s3.S3FileIO',
        's3.endpoint'='http://minio.minio:9000',
        's3.path-style-access'='true',
        's3.access-key-id'='admin',
        's3.secret-access-key'='password'
    )
    """
    t_env.execute_sql(catalog_ddl)
    
    # Create and use database
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS iceberg_catalog.chat_db")
    t_env.use_catalog("iceberg_catalog")
    t_env.use_database("chat_db")

def create_iceberg_sink(t_env):
    sink_ddl = """
    CREATE TABLE chat_messages_sink (
        stream_id STRING,
        subscription_id STRING,
        subscription_type STRING,
        message_id STRING,
        broadcaster_user_id STRING,
        broadcaster_user_name STRING,
        broadcaster_user_login STRING,
        chatter_user_id STRING,
        chatter_user_name STRING,
        chatter_user_login STRING,
        message_text STRING,
        message_type STRING,
        badges ARRAY<ROW<set_id STRING, id STRING, info STRING>>,
        source_timestamp STRING,
        processing_timestamp TIMESTAMP(3)
    ) PARTITIONED BY (broadcaster_user_id)
    WITH (
        'format-version' = '2',
        'write.upsert.enabled' = 'true',
        'warehouse' = 's3://warehouse',
        'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
        's3.endpoint' = 'http://minio.minio:9000',
        's3.access-key-id' = 'admin',
        's3.secret-key' = 'password',
        's3.path-style-access' = 'true'
    )
    """
    t_env.execute_sql(sink_ddl)

def insert_into_iceberg(t_env):
    insert_sql = """
    INSERT INTO chat_messages_sink
    SELECT 
        stream_id,
        subscription_id,
        subscription_type,
        message_id,
        broadcaster_user_id,
        broadcaster_user_name,
        broadcaster_user_login,
        chatter_user_id,
        chatter_user_name,
        chatter_user_login,
        message_text,
        message_type,
        badges,
        `timestamp` as source_timestamp,
        TO_TIMESTAMP(`timestamp`) as processing_timestamp
    FROM chat_messages
    """
    print("\nStarting data ingestion pipeline...")
    t_env.execute_sql(insert_sql)

def main():
    # Initialize environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(30000)
    
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, settings)
    
    # Configure pipeline jars
    config = t_env.get_config().get_configuration()
    config.set_string("pipeline.jars", (
        "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar;"
        "file:///opt/flink/lib/flink-sql-avro-confluent-registry-1.18.1.jar;"
        "file:///opt/flink/lib/iceberg-flink-runtime-1.18-1.5.0.jar;"
        "file:///opt/flink/lib/aws-java-sdk-bundle-1.12.608.jar"
    ))
    
    try:
        # Setup catalogs and tables
        create_iceberg_catalog(t_env)
        print("\nValidating catalog setup...")
        catalogs = t_env.execute_sql("SHOW CATALOGS").collect()
        print(f"Available catalogs: {[cat[0] for cat in catalogs]}")
        
        create_kafka_source(t_env)
        create_iceberg_sink(t_env)
        
        print("\nValidating tables...")
        tables = t_env.execute_sql("SHOW TABLES").collect()
        print(f"Available tables: {[table[0] for table in tables]}")
        
        # Start ingestion
        insert_into_iceberg(t_env)
        
        # Keep the job running
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()