from fraudshield.monitoring.kpis import compute_kpis


def test_kpis_keys_present():
    k = compute_kpis(window_days=30)
    for key in ["window_days", "total_events", "decline_rate", "challenge_rate", "allow_rate"]:
        assert key in k
