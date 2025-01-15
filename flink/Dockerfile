FROM flink:1.18.1

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:/usr/local/bin:$PATH
ENV PYTHONPATH=/opt/flink/python-scripts

RUN apt-get update -y && \
    apt-get install -y \
    python3 \
    python3-pip \
    openjdk-11-jdk \
    wget && \
    ln -sf /usr/bin/python3 /usr/local/bin/python && \
    pip3 install --no-cache-dir \
    apache-flink==1.18.1 \
    confluent-kafka \
    fastavro \
    httpx \
    pyarrow \
    avro-python3 \
    requests \
    confluent-kafka[avro] \
    pandas

RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-python/1.18.1/flink-python-1.18.1.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.0.2-1.18/flink-sql-connector-kafka-3.0.2-1.18.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.18/1.5.0/iceberg-flink-runtime-1.18-1.5.0.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-shaded-hadoop2-uber/2.8.3-1.8.3/flink-shaded-hadoop2-uber-2.8.3-1.8.3.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/hadoop/hadoop-aws/2.8.3/hadoop-aws-2.8.3.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.608/aws-java-sdk-bundle-1.12.608.jar && \
    wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-avro-confluent-registry/1.18.1/flink-sql-avro-confluent-registry-1.18.1.jar



WORKDIR /opt/flink
RUN mkdir -p /opt/flink/python-scripts
COPY python-scripts/* /opt/flink/python-scripts/
RUN chmod +x /opt/flink/python-scripts/*.py