from __future__ import annotations

import os
import sqlite3

from ..core.settings import settings


def init_db() -> None:
    """Initialize the demo SQLite database.

    In this scaffold we initialize the DB at service start for convenience.
    For real production, use migrations and a server DB (e.g., Postgres).
    """

    s = settings()

    db_dir = os.path.dirname(s.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(s.db_path)
    cur = conn.cursor()

    # Users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            home_ip TEXT,
            account_age_days INTEGER,
            vip_status TEXT,
            country TEXT
        )
        """
    )

    # Transactions
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            trans_id TEXT PRIMARY KEY,
            user_id TEXT,
            amount REAL,
            merchant TEXT,
            device_ip TEXT,
            shipping_addr TEXT,
            billing_addr TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # IP Intel
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ip_intel (
            ip_address TEXT PRIMARY KEY,
            reputation_score INTEGER,
            isp TEXT,
            is_proxy BOOLEAN
        )
        """
    )

    # KYC evidence
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS kyc_events (
            user_id TEXT,
            kyc_status TEXT,
            kyc_level TEXT,
            event_ts DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Labels / loss amounts
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chargebacks (
            trans_id TEXT,
            chargeback_amount REAL,
            reason_code TEXT,
            chargeback_date DATE
        )
        """
    )

    # User-level disputes snapshot
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS disputes (
            user_id TEXT,
            dispute_count_90d INTEGER,
            loss_amount_90d REAL,
            last_dispute_date DATE
        )
        """
    )

    # KPI tracking / decision events
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS decision_events (
            event_id TEXT PRIMARY KEY,
            trans_id TEXT,
            decision TEXT,
            risk_score REAL,
            model_version TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Seed minimal demo data
    cur.execute(
        "INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?)",
        ("U105", "Alice Smith", "alice@ex.com", "192.168.1.50", 1400, "Platinum", "US"),
    )
    cur.execute(
        "INSERT OR REPLACE INTO transactions VALUES (?,?,?,?,?,?,?,?)",
        (
            "TX-999",
            "U105",
            2800.00,
            "BestBuy",
            "45.22.19.11",
            "Freight Forwarder, DE",
            "Alice Smith, US",
            "2023-10-27 10:00:00",
        ),
    )
    cur.execute(
        "INSERT OR REPLACE INTO ip_intel VALUES (?,?,?,?)",
        ("45.22.19.11", 95, "Hostinger", 1),
    )
    cur.execute(
        "INSERT OR REPLACE INTO kyc_events VALUES (?,?,?,?)",
        ("U105", "VERIFIED", "L2", "2023-01-01 00:00:00"),
    )
    cur.execute(
        "INSERT OR REPLACE INTO disputes VALUES (?,?,?,?)",
        ("U105", 0, 0.0, None),
    )
    # Placeholder chargeback row (keeps schema exercised)
    cur.execute(
        "INSERT OR REPLACE INTO chargebacks VALUES (?,?,?,?)",
        ("TX-999", 0.0, None, None),
    )

    conn.commit()
    conn.close()
