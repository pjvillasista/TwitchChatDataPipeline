### **Project Summary and Technical Write-Up**

#### **Project Summary: Leveraging Twitch Chat Data for Insights**

The project focuses on using Twitch chat data to provide actionable insights for marketers and streamers. Given the challenges of accessing structured subscription data through Twitch EventSub due to authorization restrictions, the solution leverages chat data to identify key engagement patterns, including optimal ad timings, subscription trends, and audience activity. The system is designed to handle high message volumes, making it scalable for popular streamers like **caseoh\_** and **kaicenat**, who generate tens of thousands of messages in a few hours.

---

### **Technical Write-Up**

#### **Problem Statement**

Accessing detailed Twitch event data, such as subscriptions and gifted subs, requires broadcaster-level authorization through EventSub. This presents a significant limitation as authorization cannot be obtained directly from individual broadcasters. Additionally, high message volumes during streams create challenges for real-time data ingestion and analysis.

---

#### **Thought Process**

**1. Initial Approach (EventSub)**

- **Goal**: Use Twitch's EventSub API to retrieve structured subscription and gifting event data.
- **Challenge**: EventSub requires authorization directly from broadcasters. Without access to their credentials, obtaining this data was infeasible.

**2. Pivot to Chat Data**

- **Realization**: Twitch chat messages contain unstructured but valuable information, including notifications for subscriptions and gifted subs.
- **Decision**: Leverage chat data as the primary source for analysis, focusing on identifying patterns from the messages themselves.

**3. Handling High Message Volumes**

- **Observation**: For large streamers like caseoh\_, chat data generates ~50,000 messages in just 3 hours, excluding subscription notifications.
- **Solution**: Adopt a scalable architecture using **Kafka** to manage high-throughput data ingestion reliably.

---

#### **Solution Architecture**

**1. Data Ingestion**

- **TwitchAPI Integration**: Chat messages are streamed in real-time using TwitchAPI.
- **Kafka Producer**: Messages are sent to Kafka topics (`chat_messages`, `subscriptions`) to ensure no data loss and enable parallel processing.

**2. Data Storage**

- **MinIO**: Raw chat data is stored in MinIO as JSON or Parquet files for long-term retention and efficient querying.
- **Data Warehouse**: Summarized data is periodically transferred to a data warehouse (e.g., Snowflake, BigQuery) for analysis.

**3. Data Processing**

- **Batch Processing**: Use Spark or Python scripts to process Kafka topics, extracting key metrics such as:
  - Peak chat activity times.
  - Subscription spikes linked to specific streamer actions.
  - Patterns correlating ad performance and engagement.

**4. Insights and Visualization**

- **Dashboards**: Create Power BI/Looker dashboards to visualize key metrics, such as:
  - Engagement heatmaps by time of day.
  - Trends in subscription and gifting behavior.
  - Optimal ad placement based on audience activity.

---

#### **Key Challenges and Solutions**

1. **High Data Volumes**:

   - **Challenge**: Handling tens of thousands of messages in a short time.
   - **Solution**: Kafka’s high-throughput capabilities manage data ingestion, decoupling ingestion from processing.

2. **Unstructured Data**:

   - **Challenge**: Parsing chat messages for subscription-related events.
   - **Solution**: Use regex or NLP techniques to extract relevant data points (e.g., identifying messages indicating gifted subs).

3. **Authorization Limitations**:
   - **Challenge**: Inability to access EventSub without broadcaster consent.
   - **Solution**: Leverage chat data, which is publicly accessible and still provides valuable insights.

---

#### **Impact**

This project creates a scalable and accessible system for analyzing Twitch chat data, empowering marketers to:

- Identify **when to run ads** for maximum visibility.
- Understand audience engagement patterns during streams.  
  For streamers, it highlights **what drives subscriptions**, enabling data-driven decisions to improve audience retention and revenue.

---
