import os
import json
import asyncio
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import ChannelChatNotificationEvent, ChannelChatMessageEvent, ChannelUpdateEvent
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
from dotenv import load_dotenv
from datetime import datetime
from functools import partial


# Load environment variables
load_dotenv()


# Constants
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8090")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:29092")
NOTIFICATION_TOPIC = os.getenv("NOTIFICATION_TOPIC", "notifications")
CHAT_TOPIC = os.getenv("CHAT_TOPIC", "chat_messages")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "caseoh_")
TARGET_SCOPES = [AuthScope.USER_READ_CHAT]
CHANNEL_UPDATE_TOPIC = os.getenv("CHANNEL_UPDATE_TOPIC", "channel_updates")
# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

# Load Avro schemas
with open("schema_registry/notification_schema.avsc") as notification_schema_file:
    notification_schema = notification_schema_file.read()

with open("schema_registry/message_schema.avsc") as chat_schema_file:
    chat_message_schema = chat_schema_file.read()

with open("schema_registry/channel_update_schema.avsc") as schema_file:
    channel_update_schema = schema_file.read()

# Initialize Avro Serializers
notification_serializer = AvroSerializer(schema_registry_client, notification_schema)
chat_serializer = AvroSerializer(schema_registry_client, chat_message_schema)
channel_update_serializer = AvroSerializer(schema_registry_client, channel_update_schema)

# Initialize Kafka Producer
producer = Producer({"bootstrap.servers": KAFKA_BROKER})


def delivery_report(err, msg):
    """Delivery report callback for Kafka."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


async def fetch_current_stream_info(twitch):
    """Fetch and cache the current stream information."""
    try:
        user = await first(twitch.get_users(logins=[TARGET_CHANNEL]))
        if not user:
            print(f"User {TARGET_CHANNEL} not found")
            return None, None

        user_id = user.id
        async for stream in twitch.get_streams(user_id=[user_id]):
            print(f"Fetched stream info: stream_id={stream.id}, broadcaster_id={stream.user_id}")
            return stream.id, stream.user_id

        print(f"No active stream found for user {TARGET_CHANNEL}")
        return None, None
    except Exception as e:
        print(f"Error fetching stream info: {e}")
        return None, None


async def on_chat_message(chat_event: ChannelChatMessageEvent, stream_id: str):
    """Callback function to handle chat messages."""
    try:
        chat_event_data = chat_event.to_dict()
        message_data = {
            "stream_id": stream_id,
            "subscription_id": chat_event_data["subscription"]("id"),
            "subscription_type": chat_event_data["subscription"]("type"),
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
        key = f"{message_data['broadcaster_user_id']}_{message_data['stream_id']}"
        producer.produce(
            topic=CHAT_TOPIC,
            value=serialized_msg_data,
            key=key,
            callback=delivery_report,
        )
        print(f"Chat message published: {message_data}")
    except Exception as e:
        print(f"Error processing chat message: {e}")


async def on_chat_notification(notification_event: ChannelChatNotificationEvent, stream_id: str):
    """Handle chat notifications and publish to Kafka."""
    try:
        notification_event_data = notification_event.to_dict()
        notification_data = {
            "stream_id": stream_id,
            "subscription_id": notification_event_data["subscription"]["id"],
            "subscription_type": notification_event_data["subscription"]["type"],
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
        key = f"{notification_data['broadcaster_user_id']}_{notification_data['stream_id']}"
        producer.produce(
            topic=NOTIFICATION_TOPIC,
            value=serialized_notifications_data,
            key=key,
            callback=delivery_report,
        )
        print(f"Notification published: {notification_data}")
    except Exception as e:
        print(f"Error processing notification: {e}")


async def on_channel_update(event: ChannelUpdateEvent):
    """Callback function to handle channel updates."""
    try:
        event_data = event.to_dict()

        # Prepare channel update data
        update_data = {
            "subscription_id": event_data["subscription"]["id"],
            "broadcaster_user_id": event_data["event"]["broadcaster_user_id"],
            "broadcaster_user_name": event_data["event"]["broadcaster_user_name"],
            "title": event_data["event"]["title"],
            "language": event_data["event"]["language"],
            "category_id": event_data["event"]["category_id"],
            "category_name": event_data["event"]["category_name"],
            "content_classification_labels": event_data["event"].get("content_classification_labels", []),
            "timestamp": datetime.now().isoformat(),
        }

        # Serialize and publish to Kafka
        serialized_data = channel_update_serializer(
            update_data, SerializationContext(CHANNEL_UPDATE_TOPIC, MessageField.VALUE)
        )
        producer.produce(
            topic=CHANNEL_UPDATE_TOPIC,
            value=serialized_data,
            key=update_data["broadcaster_user_id"],
            callback=delivery_report,
        )
        producer.flush()
        print(f"Channel update published: {update_data}")

    except Exception as e:
        print(f"Error processing channel update: {e}")


async def run():
    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
    await helper.bind()

    # Fetch stream and broadcaster info
    stream_id, broadcaster_user_id = await fetch_current_stream_info(twitch)
    if not stream_id:
        print("No active stream. Exiting.")
        return
    
    user = await first(twitch.get_users())

    # Start EventSub WebSocket
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    try:
        await asyncio.gather(
            eventsub.listen_channel_chat_notification(
                broadcaster_user_id=broadcaster_user_id,
                user_id=user.id,
                callback=partial(on_chat_notification, stream_id=stream_id),
            ),
            eventsub.listen_channel_chat_message(
                broadcaster_user_id=broadcaster_user_id,
                user_id=user.id,
                callback=partial(on_chat_message, stream_id=stream_id),
            ),
            eventsub.listen_channel_update_v2(
                broadcaster_user_id=broadcaster_user_id,
                callback=partial(on_channel_update, stream_id=stream_id),
            ),
        )

        print("Listening for events... Press Ctrl+C to stop.")
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await eventsub.stop()
        await twitch.close()
        print("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Exiting program.")
