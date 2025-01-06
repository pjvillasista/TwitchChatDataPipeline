import os
import json
import asyncio
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelChatNotificationEvent, ChannelChatMessageEvent
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Constants
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8090")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:29092")
NOTIFICATION_TOPIC = os.getenv("NOTIFICATION_TOPIC", "notifications")
CHAT_TOPIC = os.getenv("CHAT_TOPIC", "chat_messages")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "kaicenat")
TARGET_SCOPES = [AuthScope.USER_READ_CHAT]

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Load Avro schemas
with open("schema_registry/notification_schema.avsc") as notification_schema_file:
    notification_schema = notification_schema_file.read()

with open("schema_registry/message_schema.avsc") as chat_schema_file:
    chat_message_schema = chat_schema_file.read()

# Initialize Avro Serializers
notification_serializer = AvroSerializer(schema_registry_client, notification_schema)
chat_serializer = AvroSerializer(schema_registry_client, chat_message_schema)

# Initialize Kafka Producer
producer = Producer({"bootstrap.servers": KAFKA_BROKER})


def delivery_report(err, msg):
    """Delivery report callback for Kafka."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


async def on_chat_message(chat_event: ChannelChatMessageEvent):
    """Callback function to handle chat messages."""
    try:
        chat_event_data = chat_event.to_dict()

        # Prepare chat message data
        message_data = {
            "message_id": chat_event_data["event"]["message_id"],
            "broadcaster_user_id": chat_event_data["event"]["broadcaster_user_id"],
            "broadcaster_user_name": chat_event_data["event"]["broadcaster_user_name"],
            "broadcaster_user_login": chat_event_data["event"]["broadcaster_user_login"],
            "chatter_user_id": chat_event_data["event"]["chatter_user_id"],
            "chatter_user_name": chat_event_data["event"]["chatter_user_name"],
            "chatter_user_login": chat_event_data["event"]["chatter_user_login"],
            "message_text": chat_event_data["event"]["message"]["text"],
            "message_type": chat_event_data["event"]["message"]["fragments"][0]["type"],
            "badges": chat_event_data["event"].get("badges", []),
            "color": chat_event_data["event"].get("color", ""),
            "timestamp": datetime.now().isoformat(),
        }

        serialized_msg_data = chat_serializer(
            message_data, SerializationContext(CHAT_TOPIC, MessageField.VALUE)
        )
        producer.produce(
            topic=CHAT_TOPIC,
            value=serialized_msg_data,
            key=message_data["broadcaster_user_id"],
            callback=delivery_report,
        )
        print(f"Chat message published: {message_data}")
    except Exception as e:
        print(f"Error processing chat message: {e}")


async def on_chat_notification(notification_event: ChannelChatNotificationEvent):
    """Handle chat notifications and publish to Kafka."""
    try:
        notification_event_data = notification_event.to_dict()

        # Prepare notification data
        notification_data = {
            "subscription_id": notification_event_data["subscription"]["id"],
            "broadcaster_user_id": notification_event_data["event"]["broadcaster_user_id"],
            "broadcaster_user_name": notification_event_data["event"]["broadcaster_user_name"],
            "broadcaster_user_login": notification_event_data["event"]["broadcaster_user_login"],
            "chatter_user_id": notification_event_data["event"]["chatter_user_id"],
            "chatter_user_name": notification_event_data["event"]["chatter_user_name"],
            "message_id": notification_event_data["event"]["message_id"],
            "message_text": notification_event_data["event"]["message"]["text"],
            "notice_type": notification_event_data["event"].get("notice_type"),
            "badges": notification_event_data["event"].get("badges", []),
            "resub": notification_event_data["event"].get("resub"),
            "timestamp": datetime.now().isoformat(),
        }

        serialized_notifications_data = notification_serializer(
            notification_data, SerializationContext(NOTIFICATION_TOPIC, MessageField.VALUE)
        )
        producer.produce(
            topic=NOTIFICATION_TOPIC,
            value=serialized_notifications_data,
            key=notification_data["broadcaster_user_id"],
            callback=delivery_report,
        )
        print(f"Notification published: {notification_data}")
    except Exception as e:
        print(f"Error processing notification: {e}")


async def get_broadcaster_id(twitch):
    """Fetch the broadcaster ID for the target channel."""
    user = await first(twitch.get_users(logins=[TARGET_CHANNEL]))
    if user:
        return user.id
    else:
        raise ValueError(f"Broadcaster '{TARGET_CHANNEL}' not found.")


async def run():
    # Initialize Twitch API with authentication helper
    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
    await helper.bind()

    # Fetch the broadcaster ID for the target channel
    broadcaster_user_id = await get_broadcaster_id(twitch)
    user = await first(twitch.get_users())

    # Start the EventSub Websocket
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    try:
        # Start WebSocket subscriptions as concurrent tasks
        chat_notification_task = asyncio.create_task(
            eventsub.listen_channel_chat_notification(
                broadcaster_user_id=broadcaster_user_id,
                user_id=user.id,
                callback=on_chat_notification,
            )
        )
        chat_message_task = asyncio.create_task(
            eventsub.listen_channel_chat_message(
                broadcaster_user_id=broadcaster_user_id,
                user_id=user.id,
                callback=on_chat_message,
            )
        )

        # Keep the program running until manually interrupted
        print("Listening for chat notifications and messages... Press Ctrl+C to stop.")
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cancel tasks and perform cleanup
        chat_notification_task.cancel()
        chat_message_task.cancel()
        await eventsub.stop()
        await twitch.close()
        print("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Exiting program.")
