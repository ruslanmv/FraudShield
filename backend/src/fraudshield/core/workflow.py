from __future__  import annotations
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..data.db import init_db
from ..tools.enrichment import (
    lookup_transaction, lookup_user_history, lookup_ip_intel, lookup_kyc, lookup_disputes, find_similar_cases_stub
)
from ..modeling.scoring import score_transaction
from ..decisioning.engine import DecisionEngine
from ..governance.audit import append_audit_jsonl
from ..governance.events import record_decision_event
from ..core.settings import settings

def build_features(trans_id: str) -> Dict[str, Any]:
    txn = lookup_transaction(trans_id)
    if not txn.get("found"):
        return {"_error": "transaction_not_found", "trans_id": trans_id}

    t = txn["transaction"]
    user_id = t.get("user_id")

    hist = lookup_user_history(user_id)
    ip = lookup_ip_intel(t.get("device_ip", ""))

    shipping = str(t.get("shipping_addr", "") or "").lower()
    billing = str(t.get("billing_addr", "") or "").lower()

    shipping_is_ff = ("freight forwarder" in shipping) or ("forwarder" in shipping)
    ship_bill_mismatch = bool(shipping) and bool(billing) and (shipping != billing)

    home_ip = str(t.get("home_ip", "") or "")
    device_ip = str(t.get("device_ip", "") or "")
    device_ip_mismatch = bool(home_ip) and bool(device_ip) and (home_ip != device_ip)

    features = {
        "trans_id": trans_id,
        "user_id": user_id,
        "amount": float(t.get("amount", 0.0) or 0.0),
        "merchant": t.get("merchant"),
        "device_ip": device_ip,
        "account_age_days": int(t.get("account_age_days", 0) or 0),
        "vip_status": t.get("vip_status"),
        "country": t.get("country"),
        "txn_count_1h": int(hist.get("velocity", {}).get("txn_count_1h", 0) or 0),
        "txn_count_24h": int(hist.get("velocity", {}).get("txn_count_24h", 0) or 0),
        "ip_reputation_score": int(ip.get("intel", {}).get("reputation_score", 0) or 0),
        "ip_is_proxy": bool(ip.get("intel", {}).get("is_proxy", False)),
        "shipping_is_freight_forwarder": shipping_is_ff,
        "ship_bill_mismatch": ship_bill_mismatch,
        "device_ip_mismatch": device_ip_mismatch,
    }
    return features

def decision_only(trans_id: str) -> Dict[str, Any]:
    features = build_features(trans_id)
    if features.get("_error"):
        return {"transaction_id": trans_id, "error": features["_error"]}

    score = score_transaction(features)
    dec = DecisionEngine().decide(features, score.risk_score)

    event_id = record_decision_event(trans_id, dec["decision"], score.risk_score, score.model_version)
    audit_path = append_audit_jsonl(
        txn_id=trans_id,
        decision=dec["decision"],
        risk_score=score.risk_score,
        model_version=score.model_version,
        reason_codes=dec["reason_codes"],
        rule_hits=dec["rule_hits"],
        extra={"decision_event_id": event_id, "api": "decision"},
    )

    return {
        "transaction_id": trans_id,
        "model_version": score.model_version,
        "risk_score": score.risk_score,
        "decision": dec["decision"],
        "reason_codes": dec["reason_codes"],
        "rule_hits": dec["rule_hits"],
        "decision_event_id": event_id,
        "audit_log_path": audit_path,
    }

def investigate_optional(trans_id: str) -> Dict[str, Any]:
    """
    Optional ops workflow. Requires `fraudshield[ops]`.
    - Agents produce artifacts and narrative.
    - Decision remains deterministic (same as decision_only).
    """
    base = decision_only(trans_id)
    if base.get("error"):
        return base

    # If ops deps not installed, return a helpful error (production-friendly)
    try:
        from ..ops.investigation import run_investigation
    except Exception as e:
        return {
            **base,
            "error": "ops_extra_not_installed",
            "message": "Install ops extras to enable investigations: `uv pip install -e \"backend[ops]\"`",
        }

    return run_investigation(trans_id, base_packet=base)
