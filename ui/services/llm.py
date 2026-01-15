from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
LLM_INDEX = "incidents-index"

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    use_ssl=False,
    verify_certs=False,
)

def fetch_latest_diagnosis():
    query = {
        "size": 1,
        "sort": [{"detected_at": {"order": "desc"}}],
        "query": {
            "exists": {
                "field": "llm_diagnosis"
            }
        },
    }

    try:
        response = client.search(
            index=LLM_INDEX,
            body=query
        )
    except NotFoundError:
        # Index not created yet
        return None

    hits = response.get("hits", {}).get("hits", [])
    if not hits:
        return None

    return hits[0]["_source"].get("llm_diagnosis")
