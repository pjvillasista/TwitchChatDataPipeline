import logging
import os
from confluent_kafka.schema_registry import Schema, SchemaRegistryClient
from confluent_kafka.schema_registry.error import SchemaRegistryError
from dotenv import load_dotenv

load_dotenv()

class SchemaClient:
    def __init__(self, schema_url, schema_subject_name, schema_str, schema_type):
        """Initialize the Schema Registry Client."""
        self.schema_url = schema_url
        self.schema_subject_name = schema_subject_name
        self.schema_str = schema_str
        self.schema_type = schema_type
        try:
            self.schema_registry_client = SchemaRegistryClient(
                {"url": self.schema_url}
            )
        except ValueError as e:
            logging.error(f"SchemaRegistryClient initialization failed: {e}")
            raise

    def get_schema_id(self):
        try:
            schema_version = self.schema_registry_client.get_latest_version(
                self.schema_subject_name
            )
            schema_id = schema_version.schema_id
            logging.info(
                f"Schema ID for {self.schema_subject_name} is {schema_id}"
            )
            return schema_id
        except SchemaRegistryError:
            return False

    def register_schema(self):
        """Register the Schema in Schema Registry."""
        try:
            self.schema_registry_client.register_schema(
                subject_name=self.schema_subject_name,
                schema=Schema(self.schema_str, schema_type=self.schema_type),
            )
            logging.info(
                f"Schema Registered Successfully for {self.schema_subject_name}"
            )
        except SchemaRegistryError as e:
            logging.error(f"Error while registering the Schema: {e}")
            exit(1)

    def set_compatibility(self, compatibility_level):
        """Update Subject Level Compatibility Level."""
        try:
            self.schema_registry_client.set_compatibility(
                self.schema_subject_name, compatibility_level
            )
            logging.info(f"Compatibility level set to {compatibility_level}")
        except SchemaRegistryError as e:
            logging.error(e)
            exit(1)


if __name__ == "__main__":
    # Load environment variables
    topic = os.environ.get("KAFKA_TOPIC")
    schema_url = os.environ.get("SCHEMA_REGISTRY_URL")
    schema_type = "AVRO"

    print(f"Schema Registry URL: {schema_url}")
    print(f"Kafka Topic: {topic}")

    # Load schema
    with open("schema_registry/subscription_schema.avsc") as avro_schema_file:
        schema_str = avro_schema_file.read()

    # Initialize Schema Client
    schema_client = SchemaClient(schema_url, topic, schema_str, schema_type)
    schema_client.set_compatibility("BACKWARD")
    schema_client.register_schema()
