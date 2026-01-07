from fraudshield.decisioning.engine import DecisionEngine

def test_rule_bias_to_challenge():
    engine = DecisionEngine()
    features = {"ip_is_proxy": True, "shipping_is_freight_forwarder": False, "ship_bill_mismatch": False}
    out = engine.decide(features, risk_score=0.2)
    assert out["decision"] == "CHALLENGE"
    assert "RULE_PROXY_SIGNAL" in out["rule_hits"]
