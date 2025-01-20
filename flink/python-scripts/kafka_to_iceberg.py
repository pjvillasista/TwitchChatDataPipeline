from pyflink.table import TableEnvironment, EnvironmentSettings

def run_ingestion():
    # Create Table Environment in batch mode
    settings = EnvironmentSettings.in_batch_mode()
    t_env = TableEnvironment.create(settings)
    
    # Configure dependencies
    config = t_env.get_config().get_configuration()
    config.set_string("pipeline.jars", (
        "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar;"
        "file:///opt/flink/lib/flink-sql-avro-confluent-registry-1.18.1.jar;"
        "file:///opt/flink/lib/iceberg-flink-runtime-1.18-1.5.0.jar"
    ))

    # Create Iceberg catalog
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
    
    print("\nConfiguring Iceberg catalog...")
    t_env.execute_sql(catalog_sql)
    t_env.use_catalog("iceberg_catalog")
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS raw_db")
    t_env.use_database("raw_db")

    # Drop existing tables if they exist
    print("\nCleaning up existing tables...")
    try:
        t_env.execute_sql("DROP TABLE IF EXISTS kafka_messages")
    except Exception as e:
        print(f"Warning while dropping kafka_messages: {str(e)}")

    # Create Kafka source table
    source_ddl = """
    CREATE TABLE kafka_messages (
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
        'topic' = 'twitch_chat_messages',
        'properties.bootstrap.servers' = 'kafka:9092',
        'properties.group.id' = 'flink-iceberg-ingest',
        'scan.startup.mode' = 'earliest-offset',
        'format' = 'avro-confluent',
        'avro-confluent.schema-registry.url' = 'http://schema-registry:8081'
    )"""
    
    # Create Iceberg sink table (if not exists)
    sink_ddl = """
    CREATE TABLE IF NOT EXISTS chat_messages (
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
        PRIMARY KEY (broadcaster_user_id, message_id) NOT ENFORCED
    ) PARTITIONED BY (broadcaster_user_id, event_date) WITH (
        'write.format.default' = 'parquet',
        'write.metadata.delete-after-commit.enabled'='true',
        'write.metadata.previous-versions-max'='10'
    )"""
    
    print("\nCreating tables...")
    t_env.execute_sql(source_ddl)
    t_env.execute_sql(sink_ddl)
    
    # Insert data with date transformation in the INSERT statement
    insert_sql = """
    INSERT INTO chat_messages
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
        DATE_FORMAT(TO_TIMESTAMP(`timestamp`), 'yyyy-MM-dd') as event_date
    FROM kafka_messages
    """
    
    print("\nStarting data ingestion...")
    t_env.execute_sql(insert_sql).wait()
    print("Data ingestion completed")

if __name__ == "__main__":
    run_ingestion()