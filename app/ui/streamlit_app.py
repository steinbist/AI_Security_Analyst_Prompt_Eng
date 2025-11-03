from __future__ import annotations
import os, textwrap, json
import requests
import streamlit as st

st.set_page_config(page_title="AI Security Analyst Assistant", layout="wide")

def _errbox(title: str, detail: str):
    with st.expander(f"⚠️ {title}", expanded=True):
        st.code(detail)

try:
    # ----- Sidebar: server config -----
    st.sidebar.header("Server")
    api_base = st.sidebar.text_input(
        "API Base URL",
        value=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
        help="Your FastAPI server root (e.g., http://127.0.0.1:8000)",
    )

    if st.sidebar.button("Check Health"):
        try:
            r = requests.get(f"{api_base.rstrip('/')}/health", timeout=10)
            st.sidebar.json(r.json())
        except Exception as ex:
            _errbox("Health check failed", f"{type(ex).__name__}: {ex}")

    st.sidebar.header("Output")
    output_format = st.sidebar.radio("Format", ["json", "markdown"], index=0)
    schema = st.sidebar.selectbox("Schema", ["risk_assessment","event_summary","policy_alignment"], index=0)

    st.sidebar.header("Context")
    time_window = st.sidebar.text_input("Time window (optional)", value="Not specified")
    inputs_selected = st.sidebar.multiselect("Inputs", ["logs","access_records","policy_text"], default=["logs","access_records","policy_text"])

    # ----- Main: input -----
    st.title("🔐 AI Security Analyst Assistant")
    sample = textwrap.dedent("""\
        Access denied for UserID 4219 at Gate 4
        Last successful login: 2025-10-31
        User clearance: Secret
        Facility requirement: Top Secret
    """)
    txt = st.text_area("Paste logs / access records / policies", value=sample, height=180)
    if st.button("Analyze", type="primary"):
        body = {
            "input_text": txt,
            "output_format": output_format,
            "schema": schema,
            "time_window": (time_window or None),
            "inputs": inputs_selected or None,
        }
        try:
            r = requests.post(f"{api_base.rstrip('/')}/analyze", json=body, timeout=60)
            st.write(f"HTTP {r.status_code}")
            ct = r.headers.get("content-type","")
            if "json" in ct:
                data = r.json()
                st.json(data)
                # Simple findings table for risk_assessment
                if isinstance(data, dict) and data.get("data", {}).get("type") == "risk_assessment":
                    rows = []
                    for f in data["data"].get("findings", []):
                        rows.append({
                            "ID": f.get("id"),
                            "Title": f.get("title"),
                            "Severity": f.get("severity"),
                            "Score": f.get("risk_score"),
                            "Confidence": f.get("confidence"),
                        })
                    if rows:
                        st.dataframe(rows, use_container_width=True)
            else:
                st.text(r.text[:4000])
        except Exception as ex:
            _errbox("Analyze failed", f"{type(ex).__name__}: {ex}")

except Exception as ex:
    # Catch ANY import/runtime error and show it on the page instead of going blank
    st.error("UI failed to render.")
    _errbox("Unhandled exception", f"{type(ex).__name__}: {ex}")
