from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
import os

# Configuration
KAFKA_BROKER = "localhost:29092"
SCHEMA_REGISTRY_URL = "http://localhost:8081"
TOPIC = "twitch_chat_messages"

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Fetch the latest schema for the topic
subject = f"{TOPIC}-value"
schema = schema_registry_client.get_latest_version(subject).schema.schema_str

# Initialize Avro Deserializer
avro_deserializer = AvroDeserializer(schema_registry_client, schema)

# Configure Kafka Consumer
consumer_conf = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "test-group",
    "auto.offset.reset": "earliest",
}
consumer = Consumer(consumer_conf)

# Consume and log messages
consumer.subscribe([TOPIC])

print(f"Listening to topic: {TOPIC}")
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        # Log raw message
        print(f"Raw message: {msg.value()}")

        # Deserialize and log data
        try:
            deserialized_data = avro_deserializer(msg.value(), SerializationContext(TOPIC, MessageField.VALUE))
            print(f"Deserialized data: {deserialized_data}")
        except Exception as e:
            print(f"Deserialization error: {e}")
except KeyboardInterrupt:
    print("Exiting consumer.")
finally:
    consumer.close()
