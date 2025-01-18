import logging
import os
from confluent_kafka.schema_registry import Schema, SchemaRegistryClient
from confluent_kafka.schema_registry.error import SchemaRegistryError

class SchemaClient:
    def __init__(self, schema_url):
        """Initialize the Schema Registry Client."""
        self.schema_url = schema_url
        self.schema_registry_client = SchemaRegistryClient({"url": self.schema_url})

    def register_schema(self, subject_name, schema_path, schema_type="AVRO"):
        """Register a schema in the Schema Registry."""
        try:
            # Load schema from file
            with open(schema_path, "r") as schema_file:
                schema_str = schema_file.read()

            # Register schema
            schema_id = self.schema_registry_client.register_schema(
                subject_name=subject_name,
                schema=Schema(schema_str, schema_type),
            )
            logging.info(f"Schema registered successfully for {subject_name} with ID {schema_id}")
            return schema_id

        except SchemaRegistryError as e:
            logging.error(f"Error registering schema for {subject_name}: {e}")
            raise e

    def set_compatibility(self, subject_name, compatibility_level="BACKWARD"):
        """Set compatibility level for a subject."""
        try:
            self.schema_registry_client.set_compatibility(subject_name, compatibility_level)
            logging.info(f"Compatibility level set to {compatibility_level} for {subject_name}")
        except SchemaRegistryError as e:
            logging.error(f"Error setting compatibility for {subject_name}: {e}")
            raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Schema Registry URL
    schema_url = os.getenv("SCHEMA_REGISTRY_URL")

    # Initialize Schema Client
    schema_client = SchemaClient(schema_url)

    # Define schemas to register
    schemas_to_register = [
        {"subject_name": "twitch_messages-value", "schema_path": "./message_schema.avsc"},
        {"subject_name": "twitch_notifications-value", "schema_path": "./notification_schema.avsc"},
        {"subject_name": "twitch_updates-value", "schema_path": "./channel_updates_schema.avsc"},
    ]


    # Register schemas and set compatibility
    for schema_info in schemas_to_register:
        subject = schema_info["subject_name"]
        schema_path = schema_info["schema_path"]

        # Register schema
        try:
            schema_id = schema_client.register_schema(subject_name=subject, schema_path=schema_path)
            schema_client.set_compatibility(subject_name=subject, compatibility_level="BACKWARD")
            logging.info(f"Schema {subject} registered with ID {schema_id} and BACKWARD compatibility.")
        except Exception as e:
            logging.error(f"Failed to register schema {subject}: {e}")
