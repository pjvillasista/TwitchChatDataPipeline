from pyspark.sql import SparkSession

# Create a Spark session
spark = SparkSession.builder \
    .appName("KafkaToMinIO") \
    .getOrCreate()

# Kafka configurations
kafka_broker = "kafka:9092"
kafka_topic = "test"

# Read from Kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_broker) \
    .option("subscribe", kafka_topic) \
    .option("startingOffsets", "earliest") \
    .option("checkpointLocation", "/home/iceberg/spark-checkpoint") \
    .load()

# Convert Kafka value column to string
messages = df.selectExpr("CAST(value AS STRING) as value")

# # Configure MinIO/S3 access
# minio_s3_path = "s3a://test/kafka-data"
# spark._jsc.hadoopConfiguration().set("fs.s3a.endpoint", "http://minio:9000")
# spark._jsc.hadoopConfiguration().set("fs.s3a.access.key", "admin")
# spark._jsc.hadoopConfiguration().set("fs.s3a.secret.key", "password")
# spark._jsc.hadoopConfiguration().set("fs.s3a.path.style.access", "true")
# spark._jsc.hadoopConfiguration().set("fs.s3a.connection.ssl.enabled", "false")

# Write the stream to MinIO
# query = messages.writeStream \
#     .outputMode("append") \
#     .format("parquet") \
#     .option("path", minio_s3_path) \
#     .option("checkpointLocation", "/tmp/spark-checkpoint") \
#     .start()

query = messages.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()


query.awaitTermination()
