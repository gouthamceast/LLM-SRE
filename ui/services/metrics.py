from opensearchpy import OpenSearch

OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
METRICS_INDEX = "metrics-index"

client = OpenSearch(
    hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
    use_ssl=False,
    verify_certs=False,
)

def fetch_latest_metrics(service: str):
    query = {
        "size": 1,
        "sort": [{"timestamp": {"order": "desc"}}],
        "query": {
            "match": {
                "service": service
            }
        }
    }

    response = client.search(
        index=METRICS_INDEX,
        body=query
    )

    hits = response["hits"]["hits"]
    if not hits:
        return None

    return hits[0]["_source"]
