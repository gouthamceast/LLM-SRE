import json
from kafka import KafkaConsumer
from opensearchpy import OpenSearch

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "metrics"
METRICS_INDEX = "metrics-index"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

opensearch = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False,
)

def create_metrics_index_if_not_exists():
    if not opensearch.indices.exists(index=METRICS_INDEX):
        mapping = {
            "mappings": {
                "properties": {
                    "service": {"type": "keyword"},
                    "latency_ms": {"type": "integer"},
                    "rps": {"type": "integer"},
                    "cpu": {"type": "integer"},
                    "error_rate": {"type": "float"},
                    "timestamp": {"type": "date"},
                }
            }
        }
        opensearch.indices.create(index=METRICS_INDEX, body=mapping)
        print(f"📁 Created index: {METRICS_INDEX}")

def main():
    print("🚀 Starting metrics consumer...")
    create_metrics_index_if_not_exists()

    for msg in consumer:
        metric = msg.value
        opensearch.index(index=METRICS_INDEX, body=metric)
        print(f"📥 Indexed metric: {metric}")

if __name__ == "__main__":
    main()
