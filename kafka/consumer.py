from confluent_kafka import Consumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

# Configuration
SCHEMA_REGISTRY_URL = "http://localhost:8090"
KAFKA_BROKER = "localhost:29092"
KAFKA_TOPIC = "twitch_subscriptions"

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Create Avro Deserializer
avro_deserializer = AvroDeserializer(schema_registry_client)

# Kafka Consumer Configuration
consumer_config = {
    "bootstrap.servers": KAFKA_BROKER,
    "group.id": "twitch-subscriptions-group",
    "auto.offset.reset": "earliest",  # Start reading from the beginning of the topic
}

# Initialize Kafka Consumer
consumer = Consumer(consumer_config)
consumer.subscribe([KAFKA_TOPIC])

print(f"Listening for messages on topic '{KAFKA_TOPIC}'...")

try:
    while True:
        msg = consumer.poll(1.0)  # Poll for messages every 1 second

        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        # Deserialize the message value using Avro
        try:
            value = avro_deserializer(msg.value(), SerializationContext(KAFKA_TOPIC, MessageField.VALUE))
            print(f"Received message: {value}")
        except Exception as e:
            print(f"Error deserializing message: {e}")

except KeyboardInterrupt:
    print("\nStopping consumer...")

finally:
    consumer.close()
