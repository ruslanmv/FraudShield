# 🛡️ FraudShield Enterprise  
### Deterministic Fraud Risk Platform with ML Scoring & Agentic Operations

<p align="center">
  <img src="assets/logo-low.png" width="96" height="96" alt="FraudShield Logo"/>
</p>

<p align="center">
  <strong>FraudShield Enterprise (v0.5.0)</strong><br/>
  Production-minded fraud risk decisioning platform
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" />
  <img src="https://img.shields.io/badge/fastapi-async-green.svg" />
  <img src="https://img.shields.io/badge/react-vite-61dafb.svg" />
  <img src="https://img.shields.io/badge/ml-sklearn-orange.svg" />
  <img src="https://img.shields.io/badge/license-Apache--2.0-brightgreen.svg" />
</p>

---

## 👤 Author

**Ruslan Magana Vsevolodovna**  
📧 contact@ruslanmv.com  

---

## 🎯 What This Project Demonstrates

**FraudShield Enterprise** demonstrates how a **large-scale payment fraud platform** is designed when:

- decisions must be **low-latency**
- outcomes must be **deterministic**
- models must be **governed**
- losses must be **owned**
- customer friction must be **measured**
- regulators must be **satisfied**

This is **not** a chatbot demo.  
This is a **risk decisioning system**.

---

## 🧠 System Narrative

### Problem Context

At scale, a payments platform must answer one question in **milliseconds**:

> **Should this transaction be allowed, challenged, or denied — while minimizing fraud losses and customer friction?**

Real-world constraints:
- Millions of transactions per day
- Rapidly evolving fraud patterns
- Delayed labels (chargebacks arrive days or weeks later)
- Strict AML / KYC requirements
- High cost of false positives on good customers

FraudShield is designed around **these constraints**, not around toy datasets.

---

## 🧱 Core Design Principles

### 1️⃣ Determinism Before Intelligence

In regulated financial systems:

- **Models do not decide**
- **Rules do not explain**
- **LLMs do not override**

FraudShield enforces strict separation of responsibilities:

| Layer | Responsibility |
|-----|---------------|
| ML Scoring | Produce calibrated risk scores |
| Rules Engine | Encode policy and risk appetite |
| Decision Engine | ALLOW / CHALLENGE / DENY |
| Agents | Explain, summarize, assist operations |
| Humans | Own thresholds and outcomes |

This reflects how **enterprise fraud platforms are actually operated**.

---

### 2️⃣ Portfolio Ownership Over Model Worship

FraudShield is **portfolio-driven**, not model-driven.

Primary KPIs:
- Decline Rate
- Challenge Rate
- Allow Rate
- Loss Rate (chargeback-linked)
- Customer friction proxy

Models are **replaceable components**, not the product itself.

---

## 🔁 End-to-End Decision Flow

```

Transaction Arrives
↓
Authoritative Feature Build
↓
Risk Scoring
├─ ML Model (if registered)
└─ Heuristic Fallback (always available)
↓
Policy Rules + Thresholds
↓
Decision: ALLOW / CHALLENGE / DENY
↓
Audit Log + KPI Event Recorded

````

### Why This Matters

- Decisions are reproducible
- Outcomes are auditable
- Failures degrade safely
- Regulators can trace every decision

---

## 🤖 Agentic Investigation (Ops-Only)

LLMs are **intentionally sandboxed**.

They are used to:
- gather evidence
- summarize signals
- assist manual review
- produce RCA narratives

They are **never allowed** to:
- approve transactions
- deny payments
- modify thresholds
- influence deterministic decisions

This reflects **enterprise AI governance standards**.

---

## 🖥️ Operations Console (React)

The React UI represents a **Risk Operations Command Center**:

- 📥 Case Queue
- 📈 Portfolio Analytics
- 🧠 Model & Rule Context
- 🔍 Investigation Artifacts
- 🔑 Secure LLM Configuration
- 🌗 Light / Dark Mode
- 🔒 PII Masking by Default

The frontend consumes **only stable APIs** — no direct database access.

---

## 🧰 Technology Stack

| Layer       | Technology        | Rationale |
|------------|------------------|-----------|
| API        | FastAPI          | Low-latency, async, typed |
| Decisioning| Python           | Deterministic logic |
| ML         | scikit-learn     | Transparent baseline |
| Agents     | CrewAI (optional)| Ops productivity |
| Frontend   | React + Vite     | Analyst UX |
| Storage    | SQLite (demo)    | Authoritative source |
| Build      | uv               | Reproducible installs |

---

## ⚡ Quickstart

```bash
make install
make run
````

* API → [http://localhost:8000](http://localhost:8000)
* UI  → [http://localhost:5173](http://localhost:5173)

Stop everything cleanly:

```bash
make stop
```

---

## 📊 KPIs & Monitoring

FraudShield tracks:

* decision distributions
* risk score trends
* transaction volume
* loss proxy via chargebacks

These align directly with how **Fraud Risk Managers** are evaluated:

> *Reduce losses without harming legitimate customers.*

---

## 🏢 Enterprise Readiness Notes

This project explicitly demonstrates:

* ownership boundaries
* safe failure modes
* explainability
* compliance-first defaults
* ML lifecycle thinking

### What Would Be Added in Full Production

* Feature store (online/offline parity)
* Postgres with read replicas
* Real-time label ingestion
* Threshold optimization loops
* Drift detection & alerts
* RBAC and audit exports

---

## 📜 License

```
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/
```

Licensed under the **Apache License, Version 2.0**.

---

<p align="center">
  <strong>FraudShield Enterprise</strong><br/>
  Designed the way real payment fraud systems are built.
</p>
```

