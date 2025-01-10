#!/bin/bash

# Set up Spark environment variables
export SPARK_HOME="/opt/spark"
export PATH="$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH"

# Ensure all required directories exist
mkdir -p /app/logs /app/checkpoints

# Start Spark with the application
if [[ "$1" == "pyspark" ]]; then
    echo "Starting PySpark shell..."
    exec pyspark
elif [[ "$1" == "submit" ]]; then
    echo "Submitting Spark job..."
    shift  # Remove 'submit' from arguments
    exec spark-submit "$@"
else
    echo "Unknown command: $1"
    echo "Usage: ./entrypoint.sh [pyspark|submit <script.py> <args>]"
    exit 1
fi
