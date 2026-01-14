from datetime import datetime, timedelta
import json
import uuid
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer


INCIDENT_COOLDOWN = timedelta(minutes=5)

active_incidents = {}


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

def is_healthy(metrics: dict) -> bool:
    return (
        metrics["latency_ms"] < 300
        and metrics["error_rate"] < 2
        and metrics["cpu"] < 70
    )

def is_incident(metrics: dict) -> bool:
    service = metrics["service"]
    now = datetime.utcnow()

    # Suppress if incident already active
    if service in active_incidents:
        last_seen = active_incidents[service]["last_seen"]
        if now - last_seen < INCIDENT_COOLDOWN:
            return False

    return (
    metrics["error_rate"] > 10
    or metrics["latency_ms"] > 800

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
    print("🚨 Incident detector running with state and feedback loop ... ")

    for msg in consumer:
        metrics = msg.value
        service = metrics["service"]
        now = datetime.utcnow()

        print(f"[METRICS] {metrics}")

        if service in active_incidents:
            active_incidents[service]["last_seen"] = now
            if is_healthy(metrics):
                print(f"✅ INCIDENT RESOLVED for {service}")
                del active_incidents[service]
                continue

        if is_incident(metrics):
            incident = build_incident(metrics)

            active_incidents[incident["service"]] = {
                "state": "OPEN",
                "created_at": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
            }

            producer.send(INCIDENTS_TOPIC, incident)
            print(f"🔥 INCIDENT OPENED: {incident}")

if __name__ == "__main__":
    main()
