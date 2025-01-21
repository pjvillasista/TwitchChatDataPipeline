from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_kafka_topic():
    # Setup Schema Registry client and deserializer
    schema_registry_conf = {'url': 'http://schema-registry:8081'}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    avro_deserializer = AvroDeserializer(schema_registry_client)

    consumer_conf = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'test-consumer-group',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(consumer_conf)
    consumer.subscribe(['twitch_chat_messages'])

    try:
        msg_count = 0
        start_time = time.time()
        logger.info("Checking for messages...")

        while time.time() - start_time < 10:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error(f"Consumer error: {msg.error()}")
                break

            msg_count += 1

            # Deserialize the entire message and log
            try:
                deserialized_msg = avro_deserializer(
                    msg.value(),
                    SerializationContext(msg.topic(), MessageField.VALUE)
                )
                logger.info("\nDeserialized message:")
                logger.info(deserialized_msg)  # Log the entire message as JSON-like object
            except Exception as e:
                logger.error(f"Error deserializing message: {e}")
                logger.info(f"Raw message: {msg.value()}")

        logger.info(f"\nFound {msg_count} messages in sample")

    finally:
        consumer.close()

if __name__ == "__main__":
    check_kafka_topic()
