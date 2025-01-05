import os
import asyncio
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, ChatMessage, ChatSub, EventData
from twitchAPI.helper import first
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
from dotenv import load_dotenv
from datetime import datetime


class TwitchKafkaProducer:
    def __init__(self):
        """Initialize TwitchKafkaProducer with necessary configurations."""
        load_dotenv()

        # Kafka and Schema Registry Configuration
        self.schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8090")
        self.kafka_broker = os.getenv("KAFKA_BROKER", "localhost:29092")
        self.target_channel = os.getenv("TARGET_CHANNEL", "jynxzi")
        self.message_topic = os.getenv("CHAT_MESSAGES_TOPIC", "twitch_chat_messages")
        self.subscription_topic = os.getenv("SUBSCRIPTIONS_TOPIC", "twitch_subscriptions")

        # Twitch API Credentials
        self.client_id = os.getenv("APP_ID")
        self.client_secret = os.getenv("APP_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError("Twitch credentials are not set.")

        # Initialize Schema Registry and Avro Serializer
        self.schema_registry_client = SchemaRegistryClient({"url": self.schema_registry_url})


        # Load schemas
        with open("schema_registry/subscription_schema.avsc") as sub_schema_file:
            subscription_schema_str = sub_schema_file.read()

        with open("schema_registry/chat_message_schema.avsc") as msg_schema_file:
            message_schema_str = msg_schema_file.read()


        # Initialize Avro Serializers
        self.subscription_serializer = AvroSerializer(self.schema_registry_client, subscription_schema_str)
        self.message_serializer = AvroSerializer(self.schema_registry_client, message_schema_str)

        # Initialize Kafka Producer
        self.producer = Producer({"bootstrap.servers": self.kafka_broker})
        
        
        # Cache for stream info
        self.stream_id = None
        self.broadcaster_id = None
    def delivery_report(self, err, msg):
        """Delivery report callback to log Kafka message delivery status."""
        if err:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


    async def fetch_current_stream_info(self, twitch):
        """Fetch and cache the current stream information."""
        try:
            user = await first(twitch.get_users(logins=[self.target_channel]))
            if not user:
                print(f"User '{self.target_channel}' not found.")
                return None

            async for stream in twitch.get_streams(user_login=[self.target_channel]):
                self.stream_id = stream.id
                self.broadcaster_id = stream.user_id
                print(f"Fetched stream info: stream_id={self.stream_id}, broadcaster_id={self.broadcaster_id}")
                return
        except Exception as e:
            print(f"Error fetching stream info: {e}")


    async def handle_ready(self, event: EventData):
        """Callback for when the bot is ready."""
        print(f"Bot is ready. Joining channel '{self.target_channel}'...")
        await event.chat.join_room(self.target_channel)



    async def handle_message(self, msg: ChatMessage):
        """Callback for Twitch chat messages."""
        try:
            # Use cached stream_id and broadcaster_id
            if not self.stream_id or not self.broadcaster_id:
                print("Stream info not available. Skipping message.")
                return

            message_data = {
                "stream_id": self.stream_id,
                "broadcaster_id": self.broadcaster_id,
                "user_id": msg.user.id,
                "message_id": msg.id,
                "message_text": msg.text,
                "bits": msg.bits,
                "hypechat": msg.hype_chat,
                "timestamp": datetime.now().isoformat(),
            }

            # Serialize the message data
            serialized_data = self.message_serializer(
                message_data, SerializationContext(self.message_topic, MessageField.VALUE)
            )

            # Produce the serialized message to Kafka
            self.producer.produce(
                topic=self.message_topic,
                value=serialized_data,
                key=self.stream_id,  # Use stream_id as the key
                callback=self.delivery_report,
            )
            self.producer.flush()

            print(f"Produced chat message: {message_data}")

        except Exception as e:
            print(f"Error processing chat message: {e}")


    async def handle_subscription(self, sub: ChatSub):
        """Callback for Twitch subscription events."""
        try:
            subscription_data = {
                "room_name": sub.room.name if sub.room and sub.room.name else "unknown",
                "sub_plan": sub.sub_plan if sub.sub_plan else "unknown",
                "sub_plan_name": sub.sub_plan_name if sub.sub_plan_name else "unknown",
                "sub_message": sub.sub_message if sub.sub_message else None,
                "system_message": sub.system_message if sub.system_message else None,
                "timestamp": datetime.now().isoformat(),
            }

            # Serialize the subscription data
            serialized_data = self.subscription_serializer(
                subscription_data, SerializationContext(self.subscription_topic, MessageField.VALUE)
            )

            # Produce the serialized data to Kafka
            self.producer.produce(
                topic=self.subscription_topic,
                value=serialized_data,
                callback=self.delivery_report,
            )
            self.producer.flush()

            print(f"Produced message: {subscription_data}")

        except Exception as e:
            print(f"Error processing subscription: {e}")


    async def listen_for_exit(self):
        """Wait for Enter key to terminate the program."""
        print("Press Enter to stop the bot...")
        await asyncio.to_thread(input)
        print("Stopping bot...")

    async def run(self):
        """Main function to initialize and run the Twitch bot."""
        # Initialize Twitch API
        twitch = await Twitch(self.client_id, self.client_secret)
        auth = UserAuthenticator(twitch, [AuthScope.CHAT_READ], force_verify=False)
        token, refresh_token = await auth.authenticate()
        await twitch.set_user_authentication(token, [AuthScope.CHAT_READ], refresh_token)


        # Fetch the stream info
        await self.fetch_current_stream_info(twitch)


        # Initialize Twitch chat
        chat = await Chat(twitch)
        chat.register_event(ChatEvent.READY, self.handle_ready)
        chat.register_event(ChatEvent.SUB, self.handle_subscription)
        chat.register_event(ChatEvent.MESSAGE, self.handle_message)


        # Start the bot
        print(f"Starting bot for channel '{self.target_channel}'...")
        try:
            chat.start()
            await self.listen_for_exit()
        except Exception as e:
            print(f"Error running bot: {e}")
        finally:
            await chat.stop()
            await twitch.close()
            print("Bot stopped.")


if __name__ == "__main__":
    producer = TwitchKafkaProducer()
    asyncio.run(producer.run())
