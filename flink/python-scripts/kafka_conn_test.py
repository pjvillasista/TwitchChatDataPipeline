from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings

def test_kafka_connection():
    # Create streaming environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)  # Set parallelism to 1 for testing
    
    # Create table environment
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, settings)
    
    # Add required JAR files and configurations
    t_env.get_config().get_configuration().set_string(
        "pipeline.jars",
        "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.2-1.18.jar;" +
        "file:///opt/flink/lib/flink-sql-avro-confluent-registry-1.18.1.jar"
    )

    # Set checkpointing and state backend configurations
    t_env.get_config().get_configuration().set_string("execution.checkpointing.interval", "10000")
    t_env.get_config().get_configuration().set_string("state.backend", "filesystem")
    t_env.get_config().get_configuration().set_string("state.checkpoints.dir", "file:///tmp/flink-checkpoints")

    source_ddl = """
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
            badges ARRAY<ROW(set_id STRING, id STRING, info STRING)>,
            color STRING,
            `timestamp` STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'twitch_chat_messages',
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'flink-test-consumer',
            'format' = 'avro-confluent',
            'avro-confluent.schema-registry.url' = 'http://schema-registry:8081',
            'scan.startup.mode' = 'earliest-offset'
        )
    """
    
    try:
        print("Creating source table...")
        t_env.execute_sql(source_ddl)
        
        print("Executing query...")
        test_query = """
            SELECT 
                message_id,
                message_text,
                chatter_user_name,
                broadcaster_user_name,
                `timestamp`
            FROM chat_messages
            LIMIT 5
        """
        
        # Execute and print results
        result = t_env.execute_sql(test_query)
        print("Query executed successfully!")
        
        # Print the results
        with result.collect() as results:
            for row in results:
                print(row)
                
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    test_kafka_connection()