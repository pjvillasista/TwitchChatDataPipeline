import os
import json
from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Kafka and Schema Registry configuration
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8090")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:29092")
NOTIFICATION_TOPIC = os.getenv("NOTIFICATION_TOPIC", "notifications")
CHAT_TOPIC = os.getenv("CHAT_TOPIC", "chat_messages")
GROUP_ID = "twitch-data-consumer"

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Load schemas
with open("../schema_registry/notification_schema.avsc") as notification_schema_file:
    notification_schema = notification_schema_file.read()

with open("../schema_registry/message_schema.avsc") as chat_schema_file:
    chat_message_schema = chat_schema_file.read()

# Initialize Avro Deserializers
notification_deserializer = AvroDeserializer(
    schema_registry_client, notification_schema
)
chat_message_deserializer = AvroDeserializer(
    schema_registry_client, chat_message_schema
)

# Initialize Kafka Consumer
consumer = Consumer(
    {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
    }
)


def consume_data(topic, deserializer):
    """Consume data from the given Kafka topic using the provided deserializer."""
    consumer.subscribe([topic])
    print(f"Subscribed to topic: {topic}")

    try:
        while True:
            msg = consumer.poll(1.0)  # Poll for messages
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            # Deserialize the message value
            data = deserializer(
                msg.value(), SerializationContext(topic, MessageField.VALUE)
            )

            # Ensure deserialized data is parsed and printed correctly
            if data:
                print(f"Consumed from {topic}: {json.dumps(data, indent=4)}")
            else:
                print(f"Warning: Received null data from topic {topic}")

    except KeyboardInterrupt:
        print("\nExiting consumer...")
    finally:
        consumer.close()


if __name__ == "__main__":
    print("Select topic to consume:")
    print("1. Notifications")
    print("2. Chat Messages")
    choice = input("Enter choice (1 or 2): ")

    if choice == "1":
        consume_data(NOTIFICATION_TOPIC, notification_deserializer)
    elif choice == "2":
        consume_data(CHAT_TOPIC, chat_message_deserializer)
    else:
        print("Invalid choice. Exiting.")
