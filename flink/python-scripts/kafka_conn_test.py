from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import time

def create_kafka_source(t_env):
    """Create Kafka source table for chat messages"""
    
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
        `timestamp` STRING,
        event_time AS TO_TIMESTAMP(`timestamp`),
        WATERMARK FOR event_time AS event_time - INTERVAL '5' SECONDS
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'twitch_chat_messages',
        'properties.bootstrap.servers' = 'kafka:9092',
        'properties.group.id' = 'flink-consumer',
        'scan.startup.mode' = 'earliest-offset',
        'format' = 'avro-confluent',
        'avro-confluent.schema-registry.url' = 'http://schema-registry:8081'
    )
    """
    
    print("\nCreating Kafka source table...")
    t_env.execute_sql(chat_source_ddl)

def create_iceberg_catalog(t_env):
    """Create Iceberg catalog using REST catalog"""
    
    # Set configuration for REST catalog
    config = t_env.get_config().get_configuration()
    config.set_string("table.exec.iceberg.fallback-snapshot-id", "-1")
    
    # Create REST catalog
    catalog_ddl = """
    CREATE CATALOG rest_catalog WITH (
        'type'='iceberg',
        'catalog-impl'='org.apache.iceberg.rest.RESTCatalog',
        'uri'='http://rest:8181',
        'warehouse'='s3://warehouse',
        'io-impl'='org.apache.iceberg.aws.s3.S3FileIO',
        's3.endpoint'='http://minio:9000',
        's3.path-style-access'='true',
        's3.access-key-id'='admin',
        's3.secret-access-key'='password'
    )
    """
    
    print("\nCreating Iceberg REST catalog...")
    t_env.execute_sql(catalog_ddl)
    t_env.use_catalog("rest_catalog")

def create_iceberg_sink(t_env):
    """Create Iceberg sink table for chat messages"""
    
    # First create the namespace/database
    print("\nCreating default namespace...")
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS `default`")
    t_env.use_database("default")
    
    sink_ddl = """
    CREATE TABLE IF NOT EXISTS chat_messages_sink (
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
        'write.upsert.enabled' = 'true'
    )
    """
    
    print("\nCreating Iceberg sink table...")
    t_env.execute_sql(sink_ddl)

def insert_into_iceberg(t_env):
    """Insert data from Kafka into Iceberg with transformations"""
    
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
        CURRENT_TIMESTAMP as processing_timestamp
    FROM chat_messages
    """
    
    print("\nStarting data ingestion pipeline...")
    t_env.execute_sql(insert_sql)

def main():
    # Create Table environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.enable_checkpointing(30000)  # 30 seconds
    
    settings = EnvironmentSettings.new_instance()\
        .in_streaming_mode()\
        .build()
    
    t_env = StreamTableEnvironment.create(env, settings)
    
    # Add required JARs
    config = t_env.get_config().get_configuration()
    config.set_string("pipeline.jars", (
        "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar;"
        "file:///opt/flink/lib/flink-sql-avro-confluent-registry-1.18.1.jar;"
        "file:///opt/flink/lib/iceberg-flink-runtime-1.18-1.5.0.jar;"
        "file:///opt/flink/lib/aws-java-sdk-bundle-1.12.608.jar"
    ))
    
    try:
        create_kafka_source(t_env)
        create_iceberg_catalog(t_env)
        create_iceberg_sink(t_env)
        insert_into_iceberg(t_env)
        
        # Keep the job running
        while True: 
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()