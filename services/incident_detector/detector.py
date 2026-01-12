import json
import uuid
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

METRICS_TOPIC = "metrics"
INCIDENTS_TOPIC = "incidents"


# Kafka Consumer for metrics
consumer = KafkaConsumer(
    METRICS_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
)

# Kafka Producer for incidents
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

def is_incident(metrics: dict) -> bool:
    """
    Simple deterministic rules.
    """
    return (
        metrics["latency_ms"] > 1000
        and metrics["error_rate"] > 5
        and metrics["cpu"] > 80
    )

def build_incident(metrics: dict) -> dict:
    return {
        "incident_id": f"INC-{uuid.uuid4().hex[:6]}",
        "service": metrics["service"],
        "severity": "HIGH",
        "symptoms": {
            "latency_ms": metrics["latency_ms"],
            "error_rate": metrics["error_rate"],
            "cpu": metrics["cpu"],
        },
        "detected_at": datetime.utcnow().isoformat(),
    }

def main():
    print("🚨 Incident detector running...")

    for msg in consumer:
        metrics = msg.value
        print(f"[METRICS] {metrics}")

        if is_incident(metrics):
            incident = build_incident(metrics)
            producer.send(INCIDENTS_TOPIC, incident)
            print(f"🔥 INCIDENT DETECTED: {incident}")

if __name__ == "__main__":
    main()
