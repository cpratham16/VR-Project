import pytest
from app.schemas.screening import calculate_phq9_severity, calculate_gad7_severity

def test_phq9_scoring():
    assert calculate_phq9_severity(0) == "Minimal"
    assert calculate_phq9_severity(4) == "Minimal"
    assert calculate_phq9_severity(5) == "Mild"
    assert calculate_phq9_severity(9) == "Mild"
    assert calculate_phq9_severity(10) == "Moderate"
    assert calculate_phq9_severity(14) == "Moderate"
    assert calculate_phq9_severity(15) == "Moderately Severe"
    assert calculate_phq9_severity(19) == "Moderately Severe"
    assert calculate_phq9_severity(20) == "Severe"

def test_gad7_scoring():
    assert calculate_gad7_severity(0) == "Minimal"
    assert calculate_gad7_severity(4) == "Minimal"
    assert calculate_gad7_severity(5) == "Mild"
    assert calculate_gad7_severity(9) == "Mild"
    assert calculate_gad7_severity(10) == "Moderate"
    assert calculate_gad7_severity(14) == "Moderate"
    assert calculate_gad7_severity(15) == "Severe"
