import json
from kafka import KafkaConsumer
from opensearchpy import OpenSearch
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "logs"
INDEX_NAME = "logs-index"


# Kafka Consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

# OpenSearch Client
opensearch = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    http_compress=True,
    use_ssl=False,
    verify_certs=False,
)

def create_index_if_not_exists():
    if not opensearch.indices.exists(index=INDEX_NAME):
        mapping = {
            "mappings": {
                "properties": {
                    "service": {"type": "keyword"},
                    "level": {"type": "keyword"},
                    "message": {"type": "text"},
                    "timestamp": {"type": "date"},
                }
            }
        }
        opensearch.indices.create(index=INDEX_NAME, body=mapping)
        print(f"✅ Created index: {INDEX_NAME}")


def main():
    print("🚀 Starting log consumer...")
    create_index_if_not_exists()

    for msg in consumer:
        log_event = msg.value
        opensearch.index(index=INDEX_NAME, body=log_event)
        print(f"📥 Indexed log: {log_event}")

if __name__ == "__main__":
    main()