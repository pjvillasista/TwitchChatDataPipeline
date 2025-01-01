# Kafka MVP - Twitch Subscriptions

To test the current setup with **Twitch subscriptions** data being sent to Kafka, follow these steps:

---

### **Steps to Test**

#### **1. Start the Kafka Stack**

Ensure your Docker Compose stack is running:

```bash
docker-compose up -d
```

---

#### **2. Create the Kafka Topic**

Run this command to create the topic `twitch_subscriptions`:

```bash
docker exec -it kafka kafka-topics --create --topic twitch_subscriptions --bootstrap-server kafka:9092 --partitions 3 --replication-factor 1
```

- **Parameters**:
  - `--partitions 3`: Splits data into 3 partitions for scalability.
  - `--replication-factor 1`: Ensures a single replica for simplicity.

---

#### **3. Run the Producer**

Run the Twitch **producer script** to start sending subscription data to Kafka:

```bash
python kafka/producer.py
```

- You’ll see messages logged in the terminal as subscriptions are processed, e.g.:
  ```
  Producing subscription to Kafka: {...}
  ```

---

#### **4. Consume and Verify Data in Kafka**

To verify data is being written to Kafka, open a Kafka console consumer:

```bash
docker exec -it kafka kafka-console-consumer --topic twitch_subscriptions --bootstrap-server kafka:9092 --from-beginning
```

- This will display all messages sent to the topic:
  ```
  {"room_name": "timthetatman", "sub_plan": "1000", ...}
  ```

---

#### **Optional: Cleanup**

After testing, you can delete the Kafka topic if needed:

```bash
docker exec -it kafka kafka-topics --delete --topic twitch_subscriptions --bootstrap-server kafka:9092
```

---

### **Expected Outcome**

- **Producer Output**: The terminal running `producer.py` should log subscription data being sent to Kafka.
- **Consumer Output**: The terminal running the `kafka-console-consumer` should display the same data, confirming successful ingestion.

## Requirements

- Python 3.8+
- Kafka setup (from the main `docker-compose.yml`)
- Twitch Developer Credentials
