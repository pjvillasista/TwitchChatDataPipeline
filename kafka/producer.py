import os
import asyncio
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, ChatSub, EventData
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Kafka and Schema Registry configuration
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8090")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "twitch_subscriptions")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "timthetatman")

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Load schema from file
with open("schema_registry/subscription_schema.avsc") as avro_schema_file:
    schema_str = avro_schema_file.read()

# Initialize Avro Serializer
avro_serializer = AvroSerializer(schema_registry_client, schema_str)

# Initialize Kafka Producer
producer = Producer({"bootstrap.servers": KAFKA_BROKER})


def delivery_report(err, msg):
    """Delivery report callback to log message delivery status."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


async def on_ready(event):
    """Callback for when the bot is ready."""
    print(f"Bot is ready. Joining channel '{TARGET_CHANNEL}'...")
    await event.chat.join_room(TARGET_CHANNEL)


async def on_sub(sub: ChatSub):
    """Handle Twitch subscription events."""
    try:
        # Prepare subscription data
        subscription_data = {
            "room_name": sub.room.name if sub.room and sub.room.name else "unknown",
            "sub_plan": sub.sub_plan if sub.sub_plan else "unknown",
            "sub_plan_name": sub.sub_plan_name if sub.sub_plan_name else "unknown",
            "sub_message": sub.sub_message if sub.sub_message else None,
            "system_message": sub.system_message if sub.system_message else None,
            "timestamp": datetime.now().isoformat(),
        }

        # Serialize data using Avro
        serialized_data = avro_serializer(
            subscription_data, SerializationContext(KAFKA_TOPIC, MessageField.VALUE)
        )

        # Produce message to Kafka
        producer.produce(
            topic=KAFKA_TOPIC,
            value=serialized_data,
            callback=delivery_report
        )
        producer.flush()

        print(f"Produced message: {subscription_data}")

    except Exception as e:
        print(f"Error processing subscription: {e}")


async def listen_for_exit():
    """Wait for Enter key to terminate the program."""
    print("Press Enter to stop the bot...")
    await asyncio.to_thread(input)
    print("Stopping bot...")


async def main():
    # Twitch credentials
    CLIENT_ID = os.getenv("APP_ID")
    CLIENT_SECRET = os.getenv("APP_SECRET")
    TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "jynxzi")

    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Twitch credentials are not set.")
        return

    # Initialize Twitch API client
    twitch = await Twitch(CLIENT_ID, CLIENT_SECRET)
    auth = UserAuthenticator(twitch, [AuthScope.CHAT_READ], force_verify=False)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, [AuthScope.CHAT_READ], refresh_token)

    # Initialize Twitch chat bot
    chat = await Chat(twitch)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.SUB, on_sub)

    # Start bot
    print(f"Starting bot for channel '{TARGET_CHANNEL}'...")
    try:
        chat.start()
        await listen_for_exit()
    except Exception as e:
        print(f"Error running bot: {e}")
    finally:
        await chat.stop()
        await twitch.close()
        print("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())