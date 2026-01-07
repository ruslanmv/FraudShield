# FraudShield-Enterprise/backend/src/fraudshield/governance/audit.py

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..core.settings import settings


def append_audit_jsonl(
    txn_id: str,
    decision: str,
    risk_score: float,
    model_version: str,
    reason_codes: List[str],
    rule_hits: List[str],
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Append an audit record to an append-only JSONL log file.

    Notes:
    - In production, prefer a write-once store (e.g., immutable bucket/table) with retention controls.
    - Do NOT store raw PII here; keep it to IDs, scores, decisions, reason codes, and metadata.
    """
    s = settings()
    os.makedirs(s.logs_path, exist_ok=True)

    path = os.path.join(s.logs_path, "decisions.jsonl")

    rec = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "transaction_id": txn_id,
        "decision": decision,
        "risk_score": float(risk_score),
        "model_version": model_version,
        "reason_codes": list(reason_codes or []),
        "rule_hits": list(rule_hits or []),
        "extra": extra or {},
    }

    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return path
