from confluent_kafka.schema_registry import SchemaRegistryClient

# Schema Registry configuration
schema_registry_conf = {"url": "http://localhost:8090"}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Delete all versions of a subject
subject = "twitch_chat_messages-value"
try:
    schema_registry_client.delete_subject(subject_name=subject)
    print(f"Deleted all versions of subject '{subject}'")
except Exception as e:
    print(f"Error deleting subject: {e}")
