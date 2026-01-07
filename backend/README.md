# FraudShield Backend (v0.1.0)

This is the backend package for the FraudShield Enterprise platform.

**Operating principle (non-negotiable for regulated risk):**
- **ML scoring + deterministic rules decide** (ALLOW / CHALLENGE / DENY)
- **LLM agents never decide**; they only perform **enrichment, summarization, and RCA narrative**.

Install profiles:
- Core (API + decisioning): `fraudshield`
- Ops (agents + Streamlit UI): `fraudshield[ops]`
- ML (train + registry baseline): `fraudshield[ml]`
- Cloud connector stubs: `fraudshield[cloud]`

Python: **3.11+**
