# Base Python image
FROM python:3.10-bullseye

# Install required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jdk \
    curl \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV SPARK_HOME="/opt/spark"
ENV SPARK_VERSION=3.5.2
ENV ICEBERG_VERSION=1.6.0
ENV PATH="$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH"

# Download and install Spark
RUN mkdir -p ${SPARK_HOME} \
    && curl https://dlcdn.apache.org/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz -o spark.tgz \
    && tar -xzf spark.tgz --strip-components=1 -C ${SPARK_HOME} \
    && rm spark.tgz

# Add Iceberg Spark runtime JAR
RUN mkdir -p ${SPARK_HOME}/jars \
    && curl https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar -Lo ${SPARK_HOME}/jars/iceberg-spark-runtime.jar

# Add Iceberg AWS bundle
RUN curl https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar -Lo ${SPARK_HOME}/jars/iceberg-aws-bundle.jar

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Copy Spark configuration
COPY spark-defaults.conf ${SPARK_HOME}/conf/spark-defaults.conf

# Entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["pyspark"]
