# Use tabulario/spark-iceberg as the base image
FROM tabulario/spark-iceberg:latest

# Set environment variables for AWS and MinIO
ENV AWS_ACCESS_KEY_ID=admin
ENV AWS_SECRET_ACCESS_KEY=password
ENV AWS_REGION=us-east-1

# Add required JARs for Kafka, Avro, and Iceberg integration
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.1/spark-sql-kafka-0-10_2.12-3.5.1.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.5.1/spark-avro_2.12-3.5.1.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.3.0/iceberg-spark-runtime-3.5_2.12-1.3.0.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-rest-client/1.3.0/iceberg-rest-client-1.3.0.jar /opt/spark/jars/

# Copy configuration files
COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf
COPY entrypoint.sh /opt/spark/bin/entrypoint.sh
RUN chmod +x /opt/spark/bin/entrypoint.sh

# Copy custom scripts and notebooks
COPY scripts /opt/spark/scripts
COPY notebooks /opt/spark/notebooks

# Install Python dependencies
COPY requirements.txt /opt/spark/
RUN pip install -r /opt/spark/requirements.txt

# Set entrypoint
ENTRYPOINT ["/opt/spark/bin/entrypoint.sh"]
