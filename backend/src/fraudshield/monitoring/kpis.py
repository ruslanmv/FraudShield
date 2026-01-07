from __future__ import annotations

import sqlite3

import pandas as pd

from ..core.settings import settings
from ..data.db import init_db


def compute_kpis(window_days: int = 30) -> dict:
    """Compute high-level portfolio KPIs from recent decision events.

    Note: `loss_rate_proxy` uses chargeback_amount/total_volume and is only as good as labels.
    """

    # Ensure schema exists (demo-friendly; production would use migrations).
    init_db()

    s = settings()
    conn = sqlite3.connect(s.db_path)

    ev = pd.read_sql(
        f"""
        SELECT decision, risk_score, model_version, timestamp
        FROM decision_events
        WHERE timestamp >= datetime('now', '-{int(window_days)} day')
        """,
        conn,
    )

    vol = pd.read_sql(
        f"""
        SELECT SUM(amount) AS total_volume
        FROM transactions
        WHERE timestamp >= datetime('now', '-{int(window_days)} day')
        """,
        conn,
    )
    total_volume = float(vol.iloc[0]["total_volume"] or 0.0) if not vol.empty else 0.0

    cb = pd.read_sql(
        """
        SELECT SUM(chargeback_amount) AS cb_amount
        FROM chargebacks
        WHERE chargeback_date IS NOT NULL
        """,
        conn,
    )
    cb_amount = float(cb.iloc[0]["cb_amount"] or 0.0) if not cb.empty else 0.0

    conn.close()

    total = int(len(ev))
    if total == 0:
        return {
            "window_days": int(window_days),
            "total_events": 0,
            "decline_rate": 0.0,
            "challenge_rate": 0.0,
            "allow_rate": 0.0,
            "total_volume": total_volume,
            "chargeback_amount": cb_amount,
            "loss_rate_proxy": (cb_amount / total_volume) if total_volume else 0.0,
        }

    counts = ev["decision"].value_counts().to_dict()
    deny = float(counts.get("DENY", 0))
    chal = float(counts.get("CHALLENGE", 0))
    allow = float(counts.get("ALLOW", 0))

    return {
        "window_days": int(window_days),
        "total_events": total,
        "decline_rate": deny / total,
        "challenge_rate": chal / total,
        "allow_rate": allow / total,
        "total_volume": total_volume,
        "chargeback_amount": cb_amount,
        "loss_rate_proxy": (cb_amount / total_volume) if total_volume else 0.0,
    }
