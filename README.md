# Twitch Data Pipeline

## **Project Focus**

This project centers on **unlocking the hidden potential of Twitch chat data** to provide actionable insights for **streamers** and **marketers**. By analyzing real-time chat messages and aggregating meaningful metrics, we aim to answer key questions like:

- **For Marketers**: When is the best time to run ads during a stream for maximum engagement?
- **For Streamers**: What actions drive the most subscriptions, gifted subs, or overall engagement?

With Twitch becoming the go-to platform for live engagement, understanding chat activity has never been more crucial. Whether it’s tracking audience behavior, optimizing ad revenue, or identifying engagement patterns, **chat data holds the key**.

---

## **The Value We Bring**

### **For Marketers**

- Identify **peak engagement times** during streams to strategically place ads.
- Analyze trends across channels to compare audience engagement.
- Understand how specific **tags, games, or content** drive higher activity or subscriptions.

### **For Streamers**

- Pinpoint **what actions drive engagement, subscriptions, and gifted subs**.
- Identify **peak activity moments** to align shoutouts, events, or calls to action.
- Track **user-specific behavior**, such as loyal viewers or churn trends.

---

## **Expanded Metrics**

Our system aggregates and tracks metrics across multiple dimensions to provide rich, actionable insights:

- **Channel Metrics**:
  - Engagement heatmaps (chat volume and activity by time).
  - Subscription and gifted sub trends during streams.
  - Comparisons of engagement and subscription patterns across channels or stream categories.
- **User Metrics**:
  - Watch time per user (based on chat activity).
  - Churn prediction (e.g., users who stop engaging over time).
  - Gifter profiles: Identifying top gifters or frequent contributors.
- **Stream Metadata Analysis**:
  - Engagement trends by **game type**, **tags**, or **streamer category**.
  - Clustering of streams by similar engagement behaviors.
- **Ad Placement Insights**:
  - Best times to run ads based on audience activity and retention patterns.
  - Correlations between ad timing and post-ad engagement levels.

---

## **Solution Architecture**

### **1. Challenges**

#### **Data Accessibility**:

- Subscription data through Twitch EventSub required broadcaster-level authorization, which was unattainable.
- Pivoted to leveraging publicly available Twitch chat data, which, while less structured, contains valuable signals for engagement and subscriptions.

#### **High Data Volume**:

- Popular streamers like caseoh\_ or kaicenat generate **50,000+ messages in 3 hours**, excluding subscription notifications.
- The initial JSON-based MVP couldn’t handle this volume, leading to data loss and inefficiency.

---

### **2. The MVP: JSON-Based Approach**

We started with a simple MVP to prove the concept:

- Chat data was collected using the **TwitchAPI** and appended to a **JSON file**.
- **Strength**: Quick to implement and demonstrated the viability of chat data analysis.
- **Limitations**:
  - Couldn’t scale to high message volumes.
  - Manual parsing was needed for insights.
  - Lacked efficient querying capabilities for analysis.

---

### **3. Lambda Architecture**

To address the MVP’s limitations, we adopted a **Lambda Architecture** that combines batch processing for analytics with a real-time component for quick insights:

#### **Data Ingestion**

- **Kafka**: Used to reliably ingest high-throughput chat messages into distinct topics:
  - `chat_messages`: For raw chat data.
  - `subscriptions`: For messages indicating subs or gifted subs.
- Kafka ensures no data loss and allows for event-time processing.

#### **Batch Layer**

- **MinIO**: Stores raw chat data as **AVRO files** for long-term durability and efficient processing.
- **Batch Processing**:
  - Aggregates chat data in **Apache Spark** or **Python** to calculate:
    - Channel-level engagement metrics (e.g., heatmaps, subscription trends).
    - User-level metrics (e.g., churn predictions, watch time).
    - Comparisons across channels by metadata (e.g., games or tags).
  - Stores summarized data in a **data warehouse** (e.g., Snowflake, BigQuery) for easy querying.

#### **Real-Time Component**

- **Real-Time Processing**:
  - For immediate insights, such as **real-time engagement spikes** during events, we use Spark Structured Streaming to consume Kafka topics and generate basic dashboards or notifications.

#### **Visualization**

- **Power BI or Looker**: Dashboards visualize metrics for marketers and streamers:
  - Engagement heatmaps by time and activity.
  - Ad placement recommendations based on activity dips/spikes.
  - User and channel-level trends.

---

## **Technical Decisions**

### **Why Lambda Architecture?**

- **Flexibility**: Combines the reliability of batch processing with the speed of real-time insights.
- **Scalability**: Can handle high data volumes while processing data both in real time and in aggregate.
- **Future-Proof**: Allows for a gradual transition to Kappa (pure streaming) if real-time analytics becomes a hard requirement.

### **Why AVRO over JSON?**

- AVRO provides:
  - **Smaller file sizes** due to binary encoding.
  - **Schema enforcement**, ensuring consistent data structure.
  - **Better performance** for serialization and deserialization.

---

## **Next Steps**

1. **Expand Metrics**:
   - Implement clustering of streams by metadata (e.g., tags or games).
   - Add user-level behavior tracking, like churn prediction or loyalty analysis.
2. **Real-Time Sentiment Analysis**:
   - Integrate keyword-based or lightweight AI models to track chat sentiment in real time.
3. **Enhance Ad Insights**:
   - Correlate ad timing with specific streamer actions to identify high-impact strategies.
4. **Consider Additional Sources**:
   - Explore integrating YouTube data for cross-platform insights.

---

## **Conclusion**

This project demonstrates how **Twitch chat data** can overcome API limitations and provide critical insights for both marketers and streamers. By combining scalable technologies like **Kafka** and **MinIO** with a **Lambda Architecture**, we’ve transformed raw chat messages into actionable intelligence.

---

Would you like to contribute or learn more? Feel free to reach out!

---

This updated `README.md` incorporates expanded metrics and keeps the **Lambda architecture** intact, while setting the stage for potential future enhancements. Let me know if you need further edits!
