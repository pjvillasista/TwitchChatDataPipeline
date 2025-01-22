from confluent_kafka.admin import AdminClient
from confluent_kafka import Consumer
import time

def check_kafka_topic():
    # Admin client to check topic
    admin_conf = {'bootstrap.servers': 'kafka:9092'}
    admin_client = AdminClient(admin_conf)
    
    # Get topic info
    topics = admin_client.list_topics(timeout=10)
    
    print("Available topics:")
    for topic in topics.topics:
        print(f"- {topic}")
        
    if 'twitch_chat_messages' not in topics.topics:
        print("\nERROR: twitch_chat_messages topic not found!")
        return
        
    # Try to count messages
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
        print("\nChecking for messages...")
        
        while time.time() - start_time < 10:  # Check for 10 seconds
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                break
            msg_count += 1
            
            # Print first message as sample
            if msg_count == 1:
                print("\nSample message:")
                print(msg.value())
        
        print(f"\nFound {msg_count} messages in 10 second sample")
        
    finally:
        consumer.close()

if __name__ == "__main__":
    check_kafka_topic()


# """
# Sample message:
# b'\x00\x00\x00\x00\x01\x02\x18314319967996\
# x02H91ee6cc6-fdc6-4aa7-925a-431268679113\
# x02(channel.chat.message\
# x02H04187365-f66f-47d6-bfd6-3f64f973a4fc
# \x02\x12411377640
# \x02\x0cJynxzi\x02\x0cjynxzi\x02\x12100135110
# \x02\x1cStreamElements\x02\x1cstreamelements\
# x02\xa0\x01@aceymogz aceymogz has 500 points and is rank 902335/2754803 on the leaderboard.
# \x02\x0emention\x04\x12moderator
# \x021\x02\x00\x0epartner\x021
# \x02\x00\x0042025-01-17T17:44:04.939974'
# """