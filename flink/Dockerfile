# Base image for Flink
FROM flink:1.16.2

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install Python, Java, and dependencies
RUN apt-get update -y && \
    apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libffi-dev liblzma-dev && \
    apt-get install -y python3 python3-pip openjdk-11-jdk && \
    mkdir -p /usr/lib/jvm/java-11-openjdk-amd64/bin && \
    if [ ! -e /usr/lib/jvm/java-11-openjdk-amd64/bin/java ]; then \
    ln -s /usr/bin/java /usr/lib/jvm/java-11-openjdk-amd64/bin/java; \
    fi && \
    pip3 install apache-flink && \
    apt-get clean


# Download required libraries
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-python/1.16.2/flink-python-1.16.2.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.16.2/flink-sql-connector-kafka-1.16.2.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-dist_2.12/1.16.2/flink-dist_2.12-1.16.2.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.16/1.5.2/iceberg-flink-runtime-1.16-1.5.2.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-shaded-hadoop2-uber/2.8.3-1.8.3/flink-shaded-hadoop2-uber-2.8.3-1.8.3.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/hadoop/hadoop-aws/2.8.3/hadoop-aws-2.8.3.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.375/aws-java-sdk-bundle-1.11.375.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/com/google/guava/guava/30.1.1-jre/guava-30.1.1-jre.jar

# Copy configuration and scripts
COPY conf /opt/flink/conf
COPY python-scripts /opt/flink/python-scripts

# Set working directory
WORKDIR /opt/flink
