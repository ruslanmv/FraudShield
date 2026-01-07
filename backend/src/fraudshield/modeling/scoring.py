# FraudShield-Enterprise/backend/src/fraudshield/modeling/scoring.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .registry import get_latest

HEURISTIC_VERSION = "heuristic_baseline_v2"


@dataclass(frozen=True)
class ScoreResult:
    risk_score: float
    model_version: str
    top_reason_codes: List[str]


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _heuristic(features: Dict[str, Any]) -> ScoreResult:
    amt = float(features.get("amount", 0.0) or 0.0)
    is_proxy = 1.0 if bool(features.get("ip_is_proxy", False)) else 0.0
    txn_1h = float(features.get("txn_count_1h", 0) or 0.0)
    acct_age = float(features.get("account_age_days", 0) or 0.0)
    ip_mismatch = 1.0 if bool(features.get("device_ip_mismatch", False)) else 0.0
    ff = 1.0 if bool(features.get("shipping_is_freight_forwarder", False)) else 0.0
    ship_bill_mismatch = 1.0 if bool(features.get("ship_bill_mismatch", False)) else 0.0

    amt_term = min(1.0, amt / 5000.0)
    vel_term = min(1.0, txn_1h / 10.0)
    age_term = 1.0 - min(1.0, acct_age / 365.0)

    score = _clip01(
        0.35 * amt_term
        + 0.20 * is_proxy
        + 0.15 * vel_term
        + 0.10 * age_term
        + 0.05 * ip_mismatch
        + 0.05 * ff
        + 0.10 * ship_bill_mismatch
    )

    reasons: List[str] = []
    if is_proxy:
        reasons.append("RC014_IP_DATACENTER_PROXY")
    if txn_1h >= 5:
        reasons.append("RC003_VELOCITY_1H_HIGH")
    if ship_bill_mismatch:
        reasons.append("RC041_SHIP_BILL_MISMATCH")
    if ff:
        reasons.append("RC031_FREIGHT_FORWARDER")
    if ip_mismatch:
        reasons.append("RC022_DEVICE_IP_MISMATCH")
    if amt >= 5000:
        reasons.append("RC010_HIGH_AMOUNT")

    return ScoreResult(risk_score=score, model_version=HEURISTIC_VERSION, top_reason_codes=reasons[:5])


def _sklearn_if_available(features: Dict[str, Any]) -> ScoreResult:
    """
    If `fraudshield[ml]` is installed and a joblib model exists, use it.
    Otherwise raise and caller will fallback to heuristic.
    """
    ptr = get_latest()
    if ptr is None:
        raise FileNotFoundError("No registered model found.")

    # joblib only available when installing `fraudshield[ml]`
    import joblib  # type: ignore

    model = joblib.load(ptr.model_path)

    # Feature order must match training (train_supervised.py)
    X = [
        [
            float(features.get("amount", 0.0) or 0.0),
            1.0 if bool(features.get("ip_is_proxy", False)) else 0.0,
            float(features.get("txn_count_1h", 0) or 0.0),
            float(features.get("account_age_days", 0) or 0.0),
            1.0 if bool(features.get("device_ip_mismatch", False)) else 0.0,
            1.0 if bool(features.get("shipping_is_freight_forwarder", False)) else 0.0,
            1.0 if bool(features.get("ship_bill_mismatch", False)) else 0.0,
        ]
    ]

    # Expect predict_proba for binary classifier
    p = float(model.predict_proba(X)[0][1])
    p = _clip01(p)

    return ScoreResult(
        risk_score=p,
        model_version=ptr.model_version,
        top_reason_codes=["RC_ML_MODEL_SCORE_USED"],
    )


def score_transaction(features: Dict[str, Any]) -> ScoreResult:
    try:
        return _sklearn_if_available(features)
    except Exception:
        return _heuristic(features)
