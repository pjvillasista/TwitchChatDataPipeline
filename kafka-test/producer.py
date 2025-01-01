import os
import asyncio
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, ChatSub, EventData
from dotenv import load_dotenv
from kafka import KafkaProducer
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Twitch API and Kafka configuration
CLIENT_ID = os.getenv("APP_ID")
CLIENT_SECRET = os.getenv("APP_SECRET")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "jynxzi")
KAFKA_BROKER = "localhost:29092"  # Kafka broker URL
KAFKA_TOPIC = "twitch_subscriptions"

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


async def on_ready(ready_event: EventData):
    """Called when the bot is ready."""
    print(f"Bot is ready and attempting to join {TARGET_CHANNEL}...")
    try:
        await asyncio.wait_for(ready_event.chat.join_room(TARGET_CHANNEL), timeout=10)
        print(f"Successfully joined channel: {TARGET_CHANNEL}")
    except asyncio.TimeoutError:
        print(f"Failed to join channel {TARGET_CHANNEL} within the timeout period.")


async def on_sub(sub: ChatSub):
    """Handle subscription events."""
    subscription_data = {
        "room_name": sub.room.name,
        "sub_plan": sub.sub_plan,
        "sub_plan_name": sub.sub_plan_name,
        "sub_message": sub.sub_message,
        "system_message": sub.system_message,
        "timestamp": datetime.now().isoformat(),
    }

    # Produce data to Kafka
    try:
        future = producer.send(KAFKA_TOPIC, value=subscription_data)
        print(f"Producing subscription to Kafka: {subscription_data}")

        # Confirm message delivery
        result = future.get(timeout=10)
        print(f"Message successfully sent to Kafka: {result}")
    except Exception as e:
        print(f"Error producing to Kafka: {e}")


async def listen_for_exit():
    """Wait for Enter key to terminate the program."""
    print("Press Enter to stop the bot...")
    await asyncio.to_thread(input)
    print("Stopping bot...")


async def main():
    # Ensure CLIENT_ID and CLIENT_SECRET are set
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: APP_ID and APP_SECRET environment variables must be set.")
        return

    # Initialize Twitch API client
    twitch = await Twitch(CLIENT_ID, CLIENT_SECRET)

    # Authenticate and set authentication for the Twitch client
    target_scope = [AuthScope.CHAT_READ]
    auth = UserAuthenticator(twitch, target_scope, force_verify=False)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, target_scope, refresh_token)

    # Initialize the Chat bot
    chat = await Chat(twitch)

    # Register events
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.SUB, on_sub)

    # Start the Chat bot
    print(f"Starting chat bot for channel '{TARGET_CHANNEL}'...")
    try:
        chat.start()
        await listen_for_exit()
    except Exception as e:
        print(f"Error during bot execution: {e}")
    finally:
        await chat.stop()
        await twitch.close()
        print("Bot has been stopped.")


if __name__ == "__main__":
    asyncio.run(main())
