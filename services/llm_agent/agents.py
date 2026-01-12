import json
from kafka import KafkaConsumer
from opensearchpy import OpenSearch
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

# ---- Config ----
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
INCIDENTS_TOPIC = "incidents"
LOG_INDEX = "logs-index"

# ---- Kafka Consumer ----
consumer = KafkaConsumer(
    INCIDENTS_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
)

# ---- OpenSearch Client ----
opensearch = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False,
)

def fetch_relevant_logs(service: str):
    query = {
        "size": 5,
        "query": {
            "bool": {
                "must": [
                    {"term": {"service": service}},
                    {"match": {"message": "connection"}}
                ]
            }
        }
    }

    response = opensearch.search(index=LOG_INDEX, body=query)
    return [hit["_source"] for hit in response["hits"]["hits"]]

def call_llm(system_prompt: str, user_prompt: str):
    """
    TEMP: Stubbed LLM response.
    We replace this with a real LLM in next step.
    """
    return {
        "root_cause": "API Gateway connection pool exhaustion under high traffic",
        "confidence": 0.85,
        "immediate_fix": "Increase connection pool size and scale replicas",
        "long_term_fix": "Introduce rate limiting and async request handling"
    }

def main():
    print("🧠 LLM Agent running...")

    for msg in consumer:
        incident = msg.value
        service = incident["service"]

        logs = fetch_relevant_logs(service)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            incident=json.dumps(incident, indent=2),
            logs=json.dumps(logs, indent=2)
        )

        llm_response = call_llm(SYSTEM_PROMPT, user_prompt)

        print("\n🧠 LLM DIAGNOSIS")
        print(json.dumps(llm_response, indent=2))

if __name__ == "__main__":
    main()