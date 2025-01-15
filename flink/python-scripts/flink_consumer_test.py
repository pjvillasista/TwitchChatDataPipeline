from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
import logging
import json

def consume_kafka():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FlinkKafkaConsumer")

    # Initialize Schema Registry client
    schema_registry_conf = {'url': 'http://schema-registry:8081'}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    # Create deserializer for the value
    value_deserializer = AvroDeserializer(schema_registry_client)

    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # Add required JARs
    env.add_jars("file:///opt/flink/lib/flink-connector-kafka_2.12-1.16.2.jar",
                 "file:///opt/flink/lib/flink-avro-1.16.2.jar")

    kafka_props = {
        "bootstrap.servers": "kafka:9092",
        "group.id": "flink-consumer-group",
        "auto.offset.reset": "earliest",
        "schema.registry.url": "http://schema-registry:8081"
    }

    kafka_consumer = FlinkKafkaConsumer(
        topics="twitch_chat_messages",
        deserialization_schema=SimpleStringSchema(),
        properties=kafka_props
    )

    stream = env.add_source(kafka_consumer)

    def process_message(message):
        try:
            # Deserialize Avro message
            deserialized_data = value_deserializer(message)
            logger.info(f"Processed message: {deserialized_data}")
            return json.dumps(deserialized_data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return str(e)

    stream.map(
        process_message,
        output_type=Types.STRING()
    ).print()

    logger.info("Starting Kafka consumer...")
    env.execute("Twitch Chat Consumer")

if __name__ == "__main__":
    consume_kafka()