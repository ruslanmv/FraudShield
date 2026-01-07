from fraudshield.core.settings import settings


def test_default_pii_flag_is_boolean():
    # Default should be false unless environment sets it
    assert isinstance(settings().include_pii, bool)
