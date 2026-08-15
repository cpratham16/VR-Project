import pytest
from app.services.risk_engine import risk_engine_service

def test_community_post_distress_scanning():
    # Test safe community post
    is_flagged, severity = risk_engine_service.scan_message_for_distress(
        "I need advice on managing time between lectures and studying for midterms."
    )
    assert is_flagged is False
    assert severity == "NONE"

    # Test community post containing self-harm signal
    is_flagged, severity = risk_engine_service.scan_message_for_distress(
        "I feel completely hopeless and want to end my life."
    )
    assert is_flagged is True
    assert severity == "CRITICAL"
