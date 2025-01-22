FROM flink:1.18.1

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:/usr/local/bin:$PATH
ENV PYTHONPATH=/opt/flink/python-scripts
ENV AWS_REGION=us-east-1


# Switch to root for installation
USER root

# Install system dependencies including Rust
RUN apt-get update -y && \
    apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    openjdk-11-jdk \
    wget \
    curl \
    build-essential && \
    ln -sf /usr/bin/python3 /usr/local/bin/python3

# Install Rust for the flink user
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install maturin before other Python packages
RUN pip3 install --no-cache-dir maturin

# Install Python packages without orjson
RUN pip3 install --no-cache-dir \
    apache-flink==1.18.1 \
    avro-python3==1.10.2 \
    confluent-kafka==2.3.0 \
    fastavro==1.9.0 \
    pyiceberg \
    typing-extensions

RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-python/1.18.1/flink-python-1.18.1.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.2-1.18/flink-sql-connector-kafka-3.0.2-1.18.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.18/1.5.0/iceberg-flink-runtime-1.18-1.5.0.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-shaded-hadoop2-uber/2.8.3-1.8.3/flink-shaded-hadoop2-uber-2.8.3-1.8.3.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.608/aws-java-sdk-bundle-1.12.608.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-avro-confluent-registry/1.18.1/flink-sql-avro-confluent-registry-1.18.1.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/hadoop/hadoop-common/3.3.4/hadoop-common-3.3.4.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws/1.5.0/iceberg-aws-1.5.0.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.20.18/bundle-2.20.18.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/software/amazon/awssdk/url-connection-client/2.20.18/url-connection-client-2.20.18.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.608/aws-java-sdk-bundle-1.12.608.jar

RUN wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/io/dropwizard/metrics/metrics-core/4.2.19/metrics-core-4.2.19.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.15.2/jackson-databind-2.15.2.jar && \
    wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.15.2/jackson-core-2.15.2.jar

RUN mkdir -p /opt/flink/plugins/s3-fs-hadoop && \
    wget -P /opt/flink/plugins/s3-fs-hadoop https://repo1.maven.org/maven2/org/apache/flink/flink-s3-fs-hadoop/1.18.1/flink-s3-fs-hadoop-1.18.1.jar

RUN chmod -R 777 /opt/flink/plugins && \
    chmod -R 777 /opt/flink/lib && \
    chown -R flink:flink /opt/flink

WORKDIR /opt/flink
RUN mkdir -p /opt/flink/python-scripts
COPY python-scripts/* /opt/flink/python-scripts/
RUN chmod +x /opt/flink/python-scripts/*.py

USER flink

CMD ["sh", "-c", "./bin/start-cluster.sh && sleep infinity"]
