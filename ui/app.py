import streamlit as st
import time
from services.metrics import fetch_latest_metrics
from services.llm import fetch_latest_diagnosis


SERVICE_NAME = "api-gateway"

st.set_page_config(
    page_title="LLM-SRE Dashboard",
    layout="wide",
)

st.title("🤖 LLM-SRE Autonomous Incident System")

st.subheader("📊 Live Service Metrics")

placeholder = st.empty()

while True:
    with placeholder.container():
        metrics = fetch_latest_metrics(SERVICE_NAME)

        if not metrics:
            st.warning("No metrics available yet...")
        else:
            latency = metrics["latency_ms"]
            error_rate = metrics["error_rate"]
            cpu = metrics["cpu"]

            # Simple health logic (same as detector, conceptually)
            if latency > 500 or error_rate > 10 or cpu > 85:
                status = "🔴 INCIDENT"
                st.error("System Status: INCIDENT")
            else:
                status = "🟢 HEALTHY"
                st.success("System Status: HEALTHY")

            col1, col2, col3 = st.columns(3)

            col1.metric("Latency (ms)", latency)
            col2.metric("Error Rate (%)", error_rate)
            col3.metric("CPU (%)", cpu)

            st.caption(f"Last updated: {metrics['timestamp']}")
            st.divider()
            st.subheader("🧠 LLM Diagnosis")

            diagnosis = fetch_latest_diagnosis()

            if not diagnosis:
                st.info("No LLM diagnosis available yet.")
            else:
                st.markdown(f"**Root Cause:** {diagnosis.get('root_cause')}")
                st.markdown(f"**Immediate Fix:** {diagnosis.get('immediate_fix')}")
                st.markdown(f"**Long-term Fix:** {diagnosis.get('long_term_fix')}")

                confidence = diagnosis.get("confidence", 0)
                st.progress(confidence)
                st.caption(f"Confidence: {int(confidence * 100)}%")

    time.sleep(2)
