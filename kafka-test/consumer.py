from kafka import KafkaConsumer
import json

KAFKA_BROKER = "localhost:29092"
KAFKA_TOPIC = "twitch_subscriptions"

# Kafka Consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
)

print(f"Listening for messages on topic '{KAFKA_TOPIC}'...")
for message in consumer:
    print(f"Received message: {message.value}")
