from __future__ import annotations

import sqlite3
import uuid

from ..core.settings import settings


def record_decision_event(
    trans_id: str, decision: str, risk_score: float, model_version: str
) -> str:
    """Persist an event for KPI computation."""

    s = settings()
    conn = sqlite3.connect(s.db_path)
    try:
        cur = conn.cursor()
        event_id = str(uuid.uuid4())
        cur.execute(
            "INSERT INTO decision_events(event_id, trans_id, decision, risk_score, model_version) "
            "VALUES(?,?,?,?,?)",
            (event_id, trans_id, decision, float(risk_score), model_version),
        )
        conn.commit()
        return event_id
    finally:
        conn.close()
