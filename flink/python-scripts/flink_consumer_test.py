from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
import logging

def consume_kafka():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FlinkKafkaConsumer")

    # Create the StreamExecutionEnvironment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # Kafka properties
    kafka_props = {
        "bootstrap.servers": "kafka:9092",  # Replace with your Kafka broker
        "group.id": "flink-test-group",
        "auto.offset.reset": "earliest",  # Consume from the earliest available message
    }

    # Create a Kafka Consumer
    kafka_consumer = FlinkKafkaConsumer(
        topics="twitch_chat_messages",                 # Kafka topic
        deserialization_schema=SimpleStringSchema(),  # String deserialization
        properties=kafka_props                        # Kafka properties
    )
    
    # Add source to the environment
    stream = env.add_source(kafka_consumer).set_parallelism(1)

    # Process the stream (print messages for this test)
    stream.map(lambda message: f"Received: {message}", output_type=Types.STRING()).print()

    # Execute the environment
    logger.info("Starting the Kafka consumer...")
    env.execute("Test Kafka Consumer")

if __name__ == "__main__":
    consume_kafka()
