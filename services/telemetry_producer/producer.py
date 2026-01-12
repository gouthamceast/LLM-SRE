import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

SERVICE_NAME = "api-gateway"



def current_time():
    return datetime.utcnow().isoformat()


def generate_metrics(step: int):
    rps = 200 + step * 150
    latency = 100 + step * 20
    cpu = min(30 + step * 5, 95)

    error_rate = 0.1
    if step > 10:
        error_rate = min(5 + step, 50)

    return {
        "service": SERVICE_NAME,
        "latency_ms": latency,
        "rps": rps,
        "cpu": cpu,
        "error_rate": error_rate,
        "timestamp": current_time(),
    }


def generate_logs(step: int):
    logs = []

    if step > 8:
        logs.append({
            "service": SERVICE_NAME,
            "level": "ERROR",
            "message": "Connection pool exhausted",
            "timestamp": current_time(),
        })

    if step > 12:
        logs.append({
            "service": SERVICE_NAME,
            "level": "ERROR",
            "message": "Upstream service timeout",
            "timestamp": current_time(),
        })

    return logs

def main():
    step = 0
    print("🚀 Starting telemetry producer...")

    while True:
        metrics = generate_metrics(step)
        producer.send("metrics", metrics)
        print(f"[METRICS] {metrics}")

        logs = generate_logs(step)
        for log in logs:
            producer.send("logs", log)
            print(f"[LOG] {log}")

        step += 1
        time.sleep(2)


if __name__ == "__main__":
    main()