FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install required Python libraries
RUN pip install confluent-kafka httpx attrs cachetools

# Copy Python script
COPY schema_registry_client.py /app/

# Copy all .avsc schema files
COPY *.avsc /app/

# Set the Schema Registry URL as an environment variable
ENV SCHEMA_REGISTRY_URL=http://schema-registry:8081

# Command to run the schema initialization script
CMD ["python3", "/app/schema_registry_client.py"]
