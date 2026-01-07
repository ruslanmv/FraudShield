# Decisioning Architecture (v0.5.0)

## Responsibilities

* **Scoring (modeling/scoring.py)**: produces `risk_score` and `model_version`
* **Decisioning (decisioning/engine.py)**: deterministic thresholds + rule hits → ALLOW/CHALLENGE/DENY
* **Governance (governance/audit.py + governance/events.py)**: immutable-ish logs + KPI events
* **Ops (ops/investigation.py)**: optional; produces RCA artifacts; never decides

## Data Contracts

Feature schema must remain consistent across training and online scoring:

* amount
* ip_is_proxy
* txn_count_1h
* account_age_days
* device_ip_mismatch
* shipping_is_freight_forwarder
* ship_bill_mismatch
