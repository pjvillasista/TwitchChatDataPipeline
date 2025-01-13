# Base image for Flink
FROM flink:1.16.2

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Install Python and dependencies
RUN apt-get update -y && \
    apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libffi-dev liblzma-dev && \
    apt-get install -y python3 python3-pip && \
    pip3 install apache-flink==1.16.2

# Download required libraries
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-python/1.16.2/flink-python-1.16.2.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.16.2/flink-sql-connector-kafka-1.16.2.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-dist_2.12/1.16.2/flink-dist_2.12-1.16.2.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/postgresql/postgresql/42.2.26/postgresql-42.2.26.jar

# Copy configuration and scripts
COPY conf /opt/flink/conf
COPY python-scripts /opt/flink/python-scripts

# Set working directory
WORKDIR /opt/flink
