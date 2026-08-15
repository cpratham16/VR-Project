import pytest
from app.services.vr_engine import calculate_stress_index

def test_stress_index_low_hr_low_hrv():
    """Resting state: low HR, healthy HRV → low stress."""
    idx = calculate_stress_index(heart_rate=65, hrv_rmssd=60)
    assert 0 <= idx <= 20

def test_stress_index_high_hr_low_hrv():
    """Elevated HR with low HRV → high stress."""
    idx = calculate_stress_index(heart_rate=110, hrv_rmssd=15)
    assert idx >= 60

def test_stress_index_no_hrv():
    """When HRV is unavailable, stress derives from HR alone."""
    idx_no_hrv = calculate_stress_index(heart_rate=90, hrv_rmssd=None)
    idx_with_hrv = calculate_stress_index(heart_rate=90, hrv_rmssd=15)
    assert idx_no_hrv >= 20
    assert idx_no_hrv != idx_with_hrv

def test_stress_index_bounded():
    """Stress index should always be 0-100."""
    for hr in [30, 60, 100, 200]:
        for hrv in [None, 5, 50, 120]:
            idx = calculate_stress_index(hr, hrv)
            assert 0 <= idx <= 100, f"Failed for hr={hr}, hrv={hrv}: {idx}"
