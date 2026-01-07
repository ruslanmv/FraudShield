from __future__ import annotations

import sqlite3
from typing import Any, Dict

import pandas as pd

from ..core.settings import settings


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(settings().db_path)


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[:1] + "*"
    else:
        masked_local = local[:1] + ("*" * (len(local) - 2)) + local[-1:]
    return f"{masked_local}@{domain}"


def _redact_user(row: Dict[str, Any]) -> Dict[str, Any]:
    """Default to PII redaction unless INCLUDE_PII=true."""
    s = settings()
    if s.include_pii:
        return row

    out = dict(row)
    if "name" in out:
        out["name"] = None
    if "email" in out:
        out["email"] = _mask_email(str(out.get("email") or ""))
    return out


def lookup_transaction(trans_id: str) -> Dict[str, Any]:
    """Return a joined transaction + user record."""
    conn = _connect()
    query = """
        SELECT
            t.trans_id,
            t.user_id,
            t.amount,
            t.merchant,
            t.device_ip,
            t.shipping_addr,
            t.billing_addr,
            t.timestamp,
            u.name,
            u.email,
            u.home_ip,
            u.account_age_days,
            u.vip_status,
            u.country
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        WHERE t.trans_id = ?
    """
    df = pd.read_sql(query, conn, params=(trans_id,))
    conn.close()

    if df.empty:
        return {"found": False, "trans_id": trans_id}

    row = _redact_user(df.iloc[0].to_dict())
    return {"found": True, "transaction": row}


def lookup_user_history(user_id: str) -> Dict[str, Any]:
    """Return recent transactions + velocity counts."""
    conn = _connect()
    q_last = """
        SELECT trans_id, amount, merchant, device_ip, timestamp
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
    """
    last_df = pd.read_sql(q_last, conn, params=(user_id,))

    q_vel = """
        SELECT
            SUM(CASE WHEN timestamp >= datetime('now','-1 hour') THEN 1 ELSE 0 END) AS txn_count_1h,
            SUM(CASE WHEN timestamp >= datetime('now','-24 hour') THEN 1 ELSE 0 END) AS txn_count_24h
        FROM transactions
        WHERE user_id = ?
    """
    vel_df = pd.read_sql(q_vel, conn, params=(user_id,))
    conn.close()

    velocity = vel_df.iloc[0].to_dict() if not vel_df.empty else {"txn_count_1h": 0, "txn_count_24h": 0}
    return {
        "user_id": user_id,
        "velocity": velocity,
        "last_transactions": last_df.to_dict(orient="records"),
    }


def lookup_ip_intel(ip: str) -> Dict[str, Any]:
    conn = _connect()
    df = pd.read_sql(
        "SELECT ip_address, reputation_score, isp, is_proxy FROM ip_intel WHERE ip_address = ?",
        conn,
        params=(ip,),
    )
    conn.close()

    if df.empty:
        return {"found": False, "ip_address": ip}
    return {"found": True, "intel": df.iloc[0].to_dict()}


def lookup_kyc(user_id: str) -> Dict[str, Any]:
    conn = _connect()
    q = """
        SELECT user_id, kyc_status, kyc_level, event_ts
        FROM kyc_events
        WHERE user_id = ?
        ORDER BY event_ts DESC
        LIMIT 1
    """
    df = pd.read_sql(q, conn, params=(user_id,))
    conn.close()

    if df.empty:
        return {"found": False, "user_id": user_id}
    return {"found": True, "kyc": df.iloc[0].to_dict()}


def lookup_disputes(user_id: str) -> Dict[str, Any]:
    conn = _connect()
    df = pd.read_sql(
        "SELECT user_id, dispute_count_90d, loss_amount_90d, last_dispute_date FROM disputes WHERE user_id = ? LIMIT 1",
        conn,
        params=(user_id,),
    )
    conn.close()

    if df.empty:
        return {"found": False, "user_id": user_id}
    return {"found": True, "disputes": df.iloc[0].to_dict()}


def find_similar_cases_stub(trans_id: str) -> Dict[str, Any]:
    """Placeholder for a kNN / ANN based similarity search."""
    return {
        "query_trans_id": trans_id,
        "similar_cases": [
            {"trans_id": "TX-888", "distance": 0.24, "reason": "Device reuse + velocity spike"},
            {"trans_id": "TX-777", "distance": 0.31, "reason": "Proxy IP + high amount"},
        ],
    }
