import json
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
INCIDENTS_TOPIC = "incidents"

CONFIDENCE_THRESHOLD = 0.7

consumer = KafkaConsumer(
    INCIDENTS_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
)

def interpret_fix(llm_response: dict):
    fix = llm_response["immediate_fix"].lower()

    actions = []

    if "scale" in fix or "replica" in fix:
        actions.append({
            "action": "scale_replicas",
            "replicas": 6
        })

    if "connection pool" in fix:
        actions.append({
            "action": "increase_connection_pool",
            "max_connections": 2000
        })

    return actions

def dry_run(actions: list):
    print("\n🧪 DRY RUN — Proposed Actions")
    for action in actions:
        print(f"  - {action}")

def apply_fix(actions: list):
    print("\n🚀 APPLYING FIX")
    for action in actions:
        print(f"✅ Executed: {action}")

def main():
    print("🤖 Hot Fix Engine running...")

    for msg in consumer:
        incident = msg.value

        # NOTE: In real system, LLM output would be attached to incident
        llm_response = {
            "confidence": 0.85,
            "immediate_fix": "Increase connection pool size and scale replicas"
        }

        if llm_response["confidence"] < CONFIDENCE_THRESHOLD:
            print("❌ Confidence too low, skipping automation")
            continue

        actions = interpret_fix(llm_response)

        if not actions:
            print("⚠️ No safe actions identified")
            continue

        dry_run(actions)

        # Simulate approval (auto-approved here)
        apply_fix(actions)

if __name__ == "__main__":
    main()
