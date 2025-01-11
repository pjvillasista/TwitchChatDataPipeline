#!/bin/bash

# Set Spark configurations dynamically
echo "Setting up Spark configurations..."
export SPARK_HOME=/opt/spark

# Start Spark Master or Worker based on mode
if [[ "$SPARK_MODE" == "master" ]]; then
  echo "Starting Spark Master..."
  /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master --host 0.0.0.0
elif [[ "$SPARK_MODE" == "worker" ]]; then
  echo "Starting Spark Worker..."
  /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker $SPARK_MASTER_URL
else
  echo "Starting Spark in standalone mode for batch or notebook execution..."
  /opt/spark/bin/spark-submit "$@"
fi
