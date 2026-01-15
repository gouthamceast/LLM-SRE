# LLM-SRE — Autonomous Incident Detection & Remediation
## Overview

LLM-SRE is an end-to-end simulation of how an SRE system can:

* Detect incidents from live telemetry
* Reason about failures using an LLM
* Apply automated remediation
* Verify recovery through feedback loops
The project focuses on system design and reliability, not just calling an LLM API.

## Why I built this

Most monitoring systems today:

* Detect an issue
* Send an alert
* Stop there

The hard part comes after:

* Digging through logs
* Guessing root cause
* Trying fixes

Checking whether the fix actually worked

This project explores:
## What if the system itself could reason about incidents and help fix them?

### High-level architecture

```js
Telemetry Producer
  ├─ sends metrics
  ├─ sends logs
  └─ simulates failures & recovery

Kafka
  ├─ metrics topic
  ├─ logs topic
  └─ incidents topic

Consumers
  ├─ metrics → OpenSearch
  ├─ logs → OpenSearch
  └─ incident detector

Incident Detector
  ├─ detects unhealthy patterns
  ├─ applies cooldowns
  └─ creates incidents with stable IDs

LLM Agent (Azure OpenAI)
  ├─ consumes incidents
  ├─ fetches related logs
  ├─ generates diagnosis
  └─ updates the incident document

Remediation Engine
  └─ simulates applying a fix

UI (Streamlit)
  └─ reads from OpenSearch
 
```

OpenSearch acts as the single source of truth for metrics, logs, and incidents.

### Incident lifecycle

1. System starts healthy
2. Latency and error rate gradually increase
3. Incident detector flags an incident
4. Incident is written to OpenSearch with a stable ID
5. LLM agent analyzes logs and metrics
6. LLM diagnosis is persisted on the incident
7. Remediation service applies a simulated fix
8. Producer enters recovery mode
9. System stabilizes
10. After cooldown, the cycle can repeat

This allows repeated, realistic incidents instead of a one-time failure.

### Components
#### Telemetry Producer

Path: services/telemetry_producer/

* Generates metrics and logs
* Simulates gradual degradation
* Supports repeated failures
* Reacts to remediation events

#### Metrics & Logs Consumers

Paths: services/metrics_consumer/
      services/log_consumer/

* Consume Kafka topics
* Index data into OpenSearch
* Create indices automatically

#### Incident Detector

Path: services/incident_detector/

* Stateful detection logic
* Cooldown to prevent alert flapping
* Emits incidents only when thresholds are crossed
* Persists incidents with stable IDs

#### LLM Agent

Path: services/llm_agent/

* Uses Azure OpenAI
* Fetches recent logs related to the incident
* Produces structured output:
    * Root cause
    * Immediate fix
    * Long-term fix
    * Confidence score
    * Uses upserts to handle race conditions safely

#### Remediation Engine

Path: services/remediation/

* Consumes LLM diagnosis output
* Simulates applying a fix
* Notifies the producer to recover

#### UI Dashboard

Path: ui/

#### Built with Streamlit

Displays:

* Live metrics
* Incident timeline
* LLM diagnosis

Handles missing or delayed data gracefully


### How to run the project
#### 1. Start infrastructure
```bash
docker compose up -d

```

#### 2. Start consumers
```bash
python services/log_consumer/consumer.py
python services/metrics_consumer/consumer.py
python services/incident_detector/detector.py

```

#### 3. Start intelligence & remediation
``` bash
python services/llm_agent/agents.py
python services/remediation/hotfix.py

```

#### 4. Start the telemetry producer
```bash
python services/telemetry_producer/producer.py
```

#### 5. Start the UI

```bash
streamlit run ui/app.py
```

### Environment variables
```env
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=2025-03-01-preview
AZURE_OPENAI_DEPLOYMENT=...
```
#### Engineering decisions

* Stable incident IDs
  Required so incidents can be updated and enriched later.

* Upserts instead of updates
  Kafka events can arrive before OpenSearch writes complete.

* Cooldown-based detection
  Prevents alert flapping and noisy incidents.

* LLM is advisory, not authoritative
  The LLM suggests fixes; the system controls execution.

### Known limitations

* Single service simulation
* Fixes are mocked
* No authentication or RBAC
* Not production hardened

These are intentional to keep the system focused and understandable.

### Possible next steps

* Support multiple services
* Add incident severity scoring
* Retry and DLQ for Kafka
* Real remediation hooks
* Alerting integrations

### Final note

This project is meant to show how LLMs fit into real operational systems, not just how to generate text.