from pyflink.table import TableEnvironment, EnvironmentSettings
import time

def create_kafka_source(t_env):
    # Create Kafka source table in default catalog with bounded reading
    chat_source_ddl = """
    CREATE TABLE default_catalog.default_database.chat_messages (
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
        'properties.group.id' = 'flink-consumer-group',
        'scan.startup.mode' = 'earliest-offset',
        'scan.bounded.mode' = 'latest-offset',
        'format' = 'avro-confluent',
        'avro-confluent.schema-registry.url' = 'http://schema-registry:8081'
    )"""
    
    try:
        print("\nCreating Kafka source table...")
        t_env.execute_sql(chat_source_ddl)
        
        # Create view with date computation
        view_sql = """
        CREATE VIEW default_catalog.default_database.chat_messages_with_date AS
        SELECT 
            *,
            DATE_FORMAT(TO_TIMESTAMP(`timestamp`), 'yyyy-MM-dd') as event_date
        FROM default_catalog.default_database.chat_messages
        """
        t_env.execute_sql(view_sql)
    except Exception as e:
        print(f"Error creating Kafka source: {str(e)}")
        raise

def configure_iceberg_catalog(t_env):
    try:
        print("\nConfiguring Iceberg catalog...")
        catalog_sql = """
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
        )"""
        t_env.execute_sql(catalog_sql)
        t_env.use_catalog("iceberg_catalog")
        
        t_env.execute_sql("CREATE DATABASE IF NOT EXISTS raw_db")
        t_env.use_database("raw_db")
        
    except Exception as e:
        print(f"Error configuring Iceberg catalog: {str(e)}")
        raise

def create_iceberg_sink(t_env):
    try:
        t_env.execute_sql("DROP TABLE IF EXISTS iceberg_catalog.raw_db.chat_messages_sink")
    except Exception as e:
        print(f"Warning while dropping existing table: {str(e)}")

    sink_ddl = """
    CREATE TABLE iceberg_catalog.raw_db.chat_messages_sink (
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
        event_date STRING,
        PRIMARY KEY (broadcaster_user_id, message_id, event_date) NOT ENFORCED
    ) PARTITIONED BY (broadcaster_user_id, event_date) WITH (
        'format-version'='2',
        'write.distribution-mode'='hash',
        'write.metadata.delete-after-commit.enabled'='true',
        'write.metadata.previous-versions-max'='10',
        'write.target-file-size-bytes'='536870912',
        'write.upsert.enabled'='true'
    )"""
    
    try:
        print("\nCreating Iceberg sink table...")
        t_env.execute_sql(sink_ddl)
    except Exception as e:
        print(f"Error creating Iceberg sink: {str(e)}")
        raise

def insert_into_iceberg(t_env):
    insert_sql = """
    INSERT INTO iceberg_catalog.raw_db.chat_messages_sink
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
        event_date
    FROM default_catalog.default_database.chat_messages_with_date
    """
    try:
        print("\nStarting data ingestion pipeline...")
        t_env.execute_sql(insert_sql)
        print("\nBatch ingestion completed successfully")
    except Exception as e:
        print(f"Error during data ingestion: {str(e)}")
        raise

def main():
    # Initialize Flink environment in batch mode
    settings = EnvironmentSettings.new_instance() \
        .in_batch_mode() \
        .build()
    
    t_env = TableEnvironment.create(settings)
    
    # Configure pipeline dependencies
    config = t_env.get_config().get_configuration()
    config.set_string("pipeline.jars", (
        "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar;"
        "file:///opt/flink/lib/flink-sql-avro-confluent-registry-1.18.1.jar;"
        "file:///opt/flink/lib/iceberg-flink-runtime-1.18-1.5.0.jar;"
        "file:///opt/flink/lib/aws-java-sdk-bundle-1.12.608.jar"
    ))
    
    try:
        # Setup pipeline components
        configure_iceberg_catalog(t_env)
        create_kafka_source(t_env)
        create_iceberg_sink(t_env)
        
        # Validate setup
        print("\nValidating setup...")
        catalogs = t_env.execute_sql("SHOW CATALOGS").collect()
        print(f"Available catalogs: {[cat[0] for cat in catalogs]}")
        
        tables = t_env.execute_sql("SHOW TABLES").collect()
        print(f"Available tables: {[table[0] for table in tables]}")
        
        # Execute batch ingestion
        insert_into_iceberg(t_env)
        print("\nBatch processing completed")
            
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()