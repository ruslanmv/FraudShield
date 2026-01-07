import streamlit as st
import requests

st.set_page_config(layout="wide", page_title="FraudShield Ops (v0.5.0)")
st.title("🛡️ FraudShield Ops Console (v0.5.0)")
st.caption("Deterministic decisions; optional agentic investigations (no decisioning).")

with st.sidebar:
    api_url = st.text_input("API URL", "http://localhost:8000")
    api_key = st.text_input("X-API-Key (optional)", type="password")
    headers = {"X-API-Key": api_key} if api_key else {}

tab1, tab2, tab3 = st.tabs(["Decision", "Investigation", "KPIs"])

with tab1:
    tx = st.text_input("Transaction ID", "TX-999", key="t1")
    if st.button("Run Decision", type="primary"):
        r = requests.post(f"{api_url}/decision", json={"trans_id": tx}, headers=headers, timeout=60)
        st.write(r.status_code)
        st.json(r.json() if r.content else {})

with tab2:
    tx = st.text_input("Transaction ID", "TX-999", key="t2")
    if st.button("Run Investigation (Agents)", type="primary"):
        r = requests.post(f"{api_url}/investigate", json={"trans_id": tx}, headers=headers, timeout=300)
        if r.status_code != 200:
            st.error(r.text)
        else:
            data = r.json()
            c1, c2, c3 = st.columns(3)
            c1.metric("Risk Score", f"{data['risk_score']:.2f}")
            c2.metric("Decision", data["decision"])
            c3.metric("Model", data["model_version"])
            st.subheader("Artifacts")
            st.code(data.get("artifacts_dir", ""))
            st.subheader("Agent Outputs")
            st.json(data.get("agent_outputs", {}))

with tab3:
    days = st.number_input("Window days", min_value=1, max_value=365, value=30)
    if st.button("Refresh KPIs"):
        r = requests.get(f"{api_url}/kpis?window_days={int(days)}", headers=headers, timeout=60)
        if r.status_code != 200:
            st.error(r.text)
        else:
            st.json(r.json())
