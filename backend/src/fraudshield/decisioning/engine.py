# FraudShield-Enterprise/backend/src/fraudshield/decisioning/engine.py

from __future__ import annotations

from typing import Any, Dict, List


class DecisionEngine:
    """
    Deterministic policy layer:
    - combines model score + rule signals
    - returns ALLOW / CHALLENGE / DENY

    Notes:
    - This layer should remain deterministic and auditable.
    - LLM outputs must not affect decisions directly.
    """

    def decide(self, features: Dict[str, Any], risk_score: float) -> Dict[str, Any]:
        rule_hits: List[str] = []
        reason_codes: List[str] = []

        # Rule signals (feature-driven)
        if bool(features.get("ip_is_proxy")):
            rule_hits.append("RULE_PROXY_SIGNAL")
            reason_codes.append("RC014_IP_DATACENTER_PROXY")

        if bool(features.get("shipping_is_freight_forwarder")):
            rule_hits.append("RULE_FREIGHT_FORWARDER_SIGNAL")
            reason_codes.append("RC031_FREIGHT_FORWARDER")

        if bool(features.get("ship_bill_mismatch")):
            rule_hits.append("RULE_SHIP_BILL_MISMATCH")
            reason_codes.append("RC041_SHIP_BILL_MISMATCH")

        # Thresholds + rule bias
        if risk_score >= 0.90:
            decision = "DENY"
            reason_codes.append("RC_ML_HIGH_RISK")
        elif risk_score >= 0.70 or len(rule_hits) > 0:
            decision = "CHALLENGE"
            if risk_score >= 0.70:
                reason_codes.append("RC_ML_MEDIUM_HIGH_RISK")
        else:
            decision = "ALLOW"

        return {
            "decision": decision,
            "rule_hits": sorted(set(rule_hits)),
            "reason_codes": sorted(set(reason_codes)),
        }
