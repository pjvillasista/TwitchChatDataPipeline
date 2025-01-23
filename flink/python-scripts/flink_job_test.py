from pyflink.table import TableEnvironment, EnvironmentSettings
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def configure_environment():
    # Switch to streaming mode
    settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(settings)
    t_env.get_config().get_configuration().set_integer("parallelism.default", 2)

    config = t_env.get_config().get_configuration()
    
    # Configure dependencies
    config.set_string("pipeline.jars", (
        "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar;"
        "file:///opt/flink/lib/flink-sql-avro-confluent-registry-1.18.1.jar;"
        "file:///opt/flink/lib/iceberg-flink-runtime-1.18-1.5.0.jar;"
        "file:///opt/flink/lib/aws-java-sdk-bundle-1.12.608.jar"
    ))
    
    # Configure checkpointing for fault tolerance
    config.set_string("execution.checkpointing.interval", "30s")
    config.set_string("execution.checkpointing.mode", "EXACTLY_ONCE")
    config.set_string("execution.checkpointing.timeout", "10min")
    config.set_string("execution.checkpointing.min-pause", "5s")
    config.set_string("execution.checkpointing.max-concurrent-checkpoints", "1")
    
    # State backend configuration
    config.set_string("state.backend", "rocksdb")
    config.set_string("state.checkpoints.dir", "file:///opt/flink/checkpoints")
    config.set_string("state.backend.incremental", "true")
    
    # MinIO/S3 Configuration
    config.set_string("s3.endpoint", "http://minio:9000")
    config.set_string("s3.path.style.access", "true")
    config.set_string("s3.access-key", "admin")
    config.set_string("s3.secret-key", "password")
    
    # AWS SDK Configuration
    config.set_string("aws.region", "us-east-1")
    config.set_string("aws.credentials.provider", "BASIC")
    config.set_string("aws.credentials.basic.accesskeyid", "admin")
    config.set_string("aws.credentials.basic.secretkey", "password")
    
    os.environ["AWS_ACCESS_KEY_ID"] = "admin"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "password"
    os.environ["AWS_REGION"] = "us-east-1"
    
    return t_env

def setup_iceberg_catalog(t_env):
    logger.info("Setting up Iceberg catalog...")
    
    catalog_sql = """
    CREATE CATALOG iceberg_catalog WITH (
        'type'='iceberg',
        'catalog-impl'='org.apache.iceberg.rest.RESTCatalog',
        'uri'='http://rest:8181',
        'warehouse'='s3://warehouse',
        'io-impl'='org.apache.iceberg.aws.s3.S3FileIO',
        's3.endpoint'='http://minio:9000',
        's3.path-style-access'='true',
        's3.access-key-id'='admin',
        's3.secret-access-key'='password',
        'aws.region'='us-east-1'
    )"""
    
    t_env.execute_sql(catalog_sql)
    t_env.use_catalog("iceberg_catalog")
    t_env.execute_sql("CREATE DATABASE IF NOT EXISTS raw_db")
    t_env.use_database("raw_db")
    
    sink_ddl = """
    CREATE TABLE IF NOT EXISTS iceberg_catalog.raw_db.raw_messages (
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
        processing_time TIMESTAMP(6),
        PRIMARY KEY (broadcaster_user_id, stream_id, message_id) NOT ENFORCED
    ) PARTITIONED BY (broadcaster_user_id, stream_id) WITH (
        'format-version' = '2',
        'write.distribution-mode' = 'hash',
        'write.metadata.delete-after-commit.enabled' = 'true',
        'write.upsert.enabled' = 'false',
        'write.parquet.compression-codec' = 'snappy',
        'write.target-file-size-bytes' = '536870912',
        'write.parquet.page-size-bytes' = '65536',
        'write.parquet.dict-size-bytes' = '2097152',
        'write.parquet.dict.enabled' = 'true',
        'write.metadata.previous-versions-max' = '10',
        'write.merge.enabled' = 'true',
        'write.merge.max-concurrent-file-group-rewrites' = '10',
        'write.merge.max-file-groups-per-rewrite' = '10'
    )"""
    
    t_env.execute_sql(sink_ddl)
    logger.info("✓ Iceberg sink table created")

def setup_kafka_source(t_env):
    logger.info("Creating Kafka source table...")
    
    source_ddl = """
    CREATE TABLE default_catalog.default_database.kafka_source (
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
        'properties.group.id' = 'flink-streaming-consumer',
        'scan.startup.mode' = 'group-offsets',
        'properties.auto.offset.reset' = 'earliest',
        'format' = 'avro-confluent',
        'avro-confluent.schema-registry.url' = 'http://schema-registry:8081'
    )"""
    
    t_env.execute_sql(source_ddl)
    logger.info("✓ Kafka source table created")

def create_continuous_query(t_env):
    logger.info("Starting continuous streaming query...")
    
    insert_sql = """
    INSERT INTO iceberg_catalog.raw_db.raw_messages
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
        CAST(LOCALTIMESTAMP AS TIMESTAMP(6)) as processing_time
    FROM default_catalog.default_database.kafka_source"""
    
    # Execute streaming insert
    statement_set = t_env.create_statement_set()
    statement_set.add_insert_sql(insert_sql)
    
    try:
        job_client = statement_set.execute().get_job_client()
        if job_client:
            execution_result = job_client.get_job_execution_result().result()
            logger.info(f"Job executed successfully: {execution_result}")
    except Exception as e:
        logger.error(f"Error executing streaming job: {str(e)}")
        raise

def main():
    try:
        t_env = configure_environment()
        setup_iceberg_catalog(t_env)
        setup_kafka_source(t_env)
        create_continuous_query(t_env)
        
        # Keep the job running
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping streaming job...")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()