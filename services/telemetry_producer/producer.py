import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka import KafkaConsumer
import threading

failure_mode = False
cooldown = 0
COOLDOWN_STEPS = 6



KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

SERVICE_NAME = "api-gateway"

def remediation_listener():
    global failure_mode, step, cooldown

    consumer = KafkaConsumer(
        "remediations",
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
    )

    for msg in consumer:
        event = msg.value
        if event.get("status") == "FIX_APPLIED":
            print("🟢 Producer entering RECOVERY mode")
            failure_mode = False
            step = 0
            cooldown = COOLDOWN_STEPS




def current_time():
    return datetime.utcnow().isoformat()


def generate_metrics(step: int):
    global failure_mode
    global has_failed_once

    latency = min(1500, 150 + step * 50)
    error_rate = min(50, step * 4)
    cpu = min(95, 30 + step * 5)

    if latency > 800 or error_rate > 30:
        failure_mode = True



    if not failure_mode:
        latency = max(200, latency)
        error_rate = max(0.5, error_rate)
        cpu = max(40, cpu)

    return {
        "service": SERVICE_NAME,
        "latency_ms": latency,
        "rps": 3000,
        "cpu": cpu,
        "error_rate": error_rate,
        "timestamp": current_time(),
    }


def generate_logs():
    global failure_mode

    if failure_mode:
        return [
            {
                "service": SERVICE_NAME,
                "level": "ERROR",
                "message": "Connection pool exhausted",
                "timestamp": current_time(),
            },
            {
                "service": SERVICE_NAME,
                "level": "ERROR",
                "message": "Upstream service timeout",
                "timestamp": current_time(),
            },
        ]

    return [
        {
            "service": SERVICE_NAME,
            "level": "INFO",
            "message": "Service operating normally",
            "timestamp": current_time(),
        }
    ]


def main():
    global cooldown, step
    step = 0
    print("🚀 Starting telemetry producer...")
    threading.Thread(target=remediation_listener, daemon=True).start()

    while True:
        metrics = generate_metrics(step)
        producer.send("metrics", metrics)
        print(f"[METRICS] {metrics}")

        logs = generate_logs()
        for log in logs:
            producer.send("logs", log)
            print(f"[LOG] {log}")

        # Cooldown period after fix
        if cooldown > 0:
            cooldown -= 1
        else:
            step += 1

        time.sleep(2)


if __name__ == "__main__":
    main()