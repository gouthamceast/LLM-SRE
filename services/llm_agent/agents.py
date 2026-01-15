import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from datetime import datetime
from kafka import KafkaConsumer
from opensearchpy import OpenSearch
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)


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
    response = client.responses.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    output_text = response.output_text
    return json.loads(output_text)




def main():
    print("🧠 LLM Agent running...")

    for msg in consumer:
        incident = msg.value
        incident_id = incident["incident_id"]
        service = incident["service"]

        logs = fetch_relevant_logs(service)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            incident=json.dumps(incident, indent=2),
            logs=json.dumps(logs, indent=2)
        )

        llm_response = call_llm(SYSTEM_PROMPT, user_prompt)

        print("\n🧠 LLM DIAGNOSIS")
        opensearch.update(
            index="incidents-index",
            id=incident_id,
            body={
                "doc": {
                    "incident_id": incident_id,
                    "service": incident["service"],
                    "severity": incident["severity"],
                    "symptoms": incident["symptoms"],
                    "detected_at": incident["detected_at"],
                    "llm_diagnosis": llm_response,
                    "diagnosed_at": datetime.utcnow().isoformat(),
                },
                "doc_as_upsert": True,  # 🔑 THIS IS THE FIX
            }
        )

        print(f"📦 Incident {incident_id} upserted with LLM diagnosis")
        print(json.dumps(llm_response, indent=2))


if __name__ == "__main__":
    main()