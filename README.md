# Twitch Data Pipeline

## **Purpose**

The Twitch Data Pipeline is designed to **capture, process, and store real-time Twitch stream data** for:

1. **Analytics**:

   - Track stream performance metrics such as viewer counts, active subscriptions, and engagement levels.
   - Analyze trends in games played, peak viewer counts, and subscription activity.

2. **Insights for Streamers**:

   - Help streamers understand their audience behavior, peak activity periods, and subscription patterns.
   - Provide actionable insights to optimize their streaming strategies.

3. **Historical Data**:
   - Maintain a **persistent history** of stream data for longitudinal analysis.
   - Support data-driven decisions for Twitch users and content creators.

---

## **Goals**

1. **Real-Time Data Collection**:

   - Capture key Twitch events such as:
     - Viewer counts.
     - Games played.
     - Chat messages.
     - Subscriptions and subscription messages.

2. **Batch Processing and Storage**:

   - Use Kafka to buffer incoming data.
   - Process data in **batches** for storage into:
     - **PostgreSQL**: Structured data for querying and reporting.
     - **MinIO**: Raw data lake for long-term storage.

3. **Data Integrity and Scalability**:

   - Implement a **Write-Audit-Publish (WAP)** pattern to ensure data is accurate and reliable.
   - Build a scalable pipeline to handle high data volumes from popular streamers like KaiCenat or CaseOh.

4. **Enable Insights and Visualization**:
   - Provide processed data for real-time dashboards and historical analysis using tools like Grafana or Power BI.

---

## **Flow/Plan**

### **1. Data Ingestion**

- **Twitch API**:

  - Extract real-time data from Twitch, including:
    - **Stream info**: Current game, viewer counts, language, etc.
    - **Chat messages**: Viewer engagement and activity.
    - **Subscription events**: Tier levels, messages, and timestamps.

- **Kafka**:
  - Use Kafka as a buffer for high-throughput, real-time data streams.
  - Ensure data is partitioned by topics (e.g., `twitch_subscriptions`, `twitch_messages`) for scalability.

---

### **2. Data Storage**

- **PostgreSQL**:

  - Store cleaned and structured data for:
    - Querying subscription trends.
    - Calculating metrics like average viewer counts or engagement levels.
    - Providing a relational database for dashboard tools.

- **MinIO**:
  - Persist raw data as JSON files in a data lake.
  - Enable replayability and support advanced analytics like ML modeling or historical trends.

---

### **3. Data Processing**

- **Batch Processing**:

  - Use Python to process Kafka messages in batches.
  - Perform validation (e.g., deduplication, schema checks) before storage.

- **Aggregation and Metrics**:
  - Compute key metrics such as:
    - Subscriptions per hour.
    - Viewer count trends during a stream.
    - Engagement rates from chat messages.

---

### **4. Data Publication**

- **Dashboards**:

  - Use PostgreSQL as a data source for Grafana or Power BI to visualize:
    - Subscription and viewer trends.
    - Chat message frequency and sentiment analysis.
  - Example visualizations:
    - Viewer count over time.
    - Breakdown of subscription tiers.
    - Active chat participants per hour.

- **Data Lake Access**:
  - Expose raw data from MinIO for advanced users and ML pipelines.

---

### **Project Components**

1. **Kafka Producer**:

   - Captures Twitch data and sends it to Kafka topics.

2. **Dual Storage Kafka Consumer**:

   - Processes Kafka messages in batches.
   - Stores structured data in PostgreSQL and raw data in MinIO.

3. **Data Pipeline**:

   - Ensures Write-Audit-Publish (WAP) for reliable data storage.

4. **Visualization Layer**:
   - Tools like Grafana and Power BI for dashboards and insights.

---

### **How to Run**

1. **Start the Pipeline**:

   - Use Docker Compose to spin up Kafka, PostgreSQL, and MinIO:
     ```bash
     docker-compose up -d
     ```

2. **Run the Producer**:

   - Capture Twitch subscription data:
     ```bash
     python kafka-test/producer.py
     ```

3. **Run the Consumer**:

   - Process and store data in PostgreSQL and MinIO:
     ```bash
     python kafka-test/dual_consumer.py
     ```

4. **Verify Data**:
   - PostgreSQL:
     ```bash
     psql -h localhost -p 5431 -U postgres -d twitch_db
     SELECT * FROM subscriptions;
     ```
   - MinIO:
     - Open `http://localhost:9001` and verify files in the `twitch-data` bucket.

---

### **Future Improvements**

1. **Real-Time Analytics**:

   - Implement a real-time dashboard for viewer and subscription metrics.

2. **Advanced Metrics**:

   - Perform sentiment analysis on chat messages.
   - Identify peak activity hours across multiple streams.

3. **Automation**:
   - Use Apache Airflow for orchestrating and scheduling batch jobs.
