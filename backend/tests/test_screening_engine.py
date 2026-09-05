"""D2 Screening Engine tests.

Acceptance criterion: a new validated scale can be added via config alone,
with no code rebuild â€” proven here by scoring a synthetic instrument.
"""
from datetime import datetime, timedelta

import pytest

from app.services.screening_engine import (
    screening_engine_service as engine,
    REMINDER_INTERVAL_DAYS_DEFAULT,
    REMINDER_INTERVAL_DAYS_ELEVATED,
)
from app.schemas.screening import calculate_phq9_severity, calculate_gad7_severity
from app.seed_screening import PHQ9, GAD7


class FakeInstrument:
    """Minimal config-only instrument stand-in (mirrors the model's JSON fields)."""

    def __init__(self, cfg):
        self.code = cfg["code"]
        self.questions = cfg["questions"]
        self.scoring_bands = cfg["scoring_bands"]
        self.answer_min = cfg["answer_min"]
        self.answer_max = cfg["answer_max"]
        self.critical_items = cfg.get("critical_items", [])


# ---------- parity: engine vs legacy calculators ----------

def _vector_for_total(total, n, max_val=3):
    """Build an n-item answer vector (0..max_val) summing to `total`."""
    base = [total // n] * n
    remainder = total - sum(base)
    i = 0
    while remainder > 0:
        if base[i] < max_val:
            base[i] += 1
            remainder -= 1
        i = (i + 1) % n
    return base


def test_phq9_band_parity_full_range():
    instr = FakeInstrument(PHQ9)
    for total in range(0, 28):
        _, band = engine.score(_vector_for_total(total, 9), instr)
        assert band == calculate_phq9_severity(total), f"score {total}: {band}"


def test_gad7_band_parity_full_range():
    instr = FakeInstrument(GAD7)
    for total in range(0, 22):
        _, band = engine.score(_vector_for_total(total, 7), instr)
        assert band == calculate_gad7_severity(total), f"score {total}: {band}"


def test_band_edge_cases_exact_boundaries():
    instr = FakeInstrument(PHQ9)
    cases = {4: "Minimal", 5: "Mild", 9: "Mild", 10: "Moderate",
             14: "Moderate", 15: "Moderately Severe", 19: "Moderately Severe", 20: "Severe"}
    for total, expected in cases.items():
        _, band = engine.score(_vector_for_total(total, 9), instr)
        assert band == expected, f"score {total} -> {band}, want {expected}"


# ---------- acceptance: new scale via config only ----------

def test_new_scale_added_via_config_without_code_changes():
    """A brand-new validated scale (PSS-4-style) defined purely as configuration."""
    pss4_cfg = {
        "code": "PSS-4",
        "title": "Perceived Stress Scale-4",
        "instructions": "In the last month, how often...?",
        "options": ["Never", "Almost never", "Sometimes", "Fairly often"],
        "questions": [
            {"id": 1, "text": "Felt unable to control important things"},
            {"id": 2, "text": "Confident about handling personal problems"},
            {"id": 3, "text": "Felt things were going your way"},
            {"id": 4, "text": "Difficulties were piling up so high you could not overcome them"},
        ],
        "scoring_bands": [
            {"max_score": 6, "label": "Low Stress"},
            {"max_score": 10, "label": "Medium Stress"},
            {"max_score": 16, "label": "High Stress"},
        ],
        "answer_min": 0,
        "answer_max": 3,
        "critical_items": [],
    }
    instr = FakeInstrument(pss4_cfg)
    assert engine.score([0, 0, 0, 0], instr) == (0, "Low Stress")
    assert engine.score([3, 3, 2, 2], instr)[1] == "Medium Stress"
    assert engine.score([3, 3, 3, 3], instr) == (12, "High Stress")
    # validation respects its own config
    with pytest.raises(ValueError):
        engine.validate_answers([0, 0], instr)


# ---------- validation ----------

def test_validation_rejects_wrong_length():
    instr = FakeInstrument(GAD7)
    with pytest.raises(ValueError):
        engine.validate_answers([0] * 8, instr)


def test_validation_rejects_out_of_range_answers():
    instr = FakeInstrument(GAD7)
    with pytest.raises(ValueError):
        engine.validate_answers([0, 0, 4, 0, 0, 0, 0], instr)
    with pytest.raises(ValueError):
        engine.validate_answers([-1, 0, 0, 0, 0, 0, 0], instr)


# ---------- critical items (PHQ-9 item 9 self-harm) ----------

def test_critical_item_flags_when_positive():
    instr = FakeInstrument(PHQ9)
    answers = [0] * 8 + [1]          # item 9 = 1, total score is just 1 -> Minimal
    assert engine.check_critical_items(answers, instr) is True


def test_critical_item_not_flagged_when_zero():
    instr = FakeInstrument(PHQ9)
    answers = [3] * 9                # Severe total but item 9 = 0? no: all 3s includes item 9=3
    # use high scores except item 9 zeroed out
    answers = [3] * 8 + [0]
    assert engine.check_critical_items(answers, instr) is False


# ---------- trends ----------

def test_detect_trend_directions():
    assert engine.detect_trend(10, 14) == "worsened"
    assert engine.detect_trend(14, 10) == "improved"
    assert engine.detect_trend(12, 12) == "stable"


class FakeResult:
    def __init__(self, screening_type, total_score, severity_band, created_at):
        self.screening_type = screening_type
        self.total_score = total_score
        self.severity_band = severity_band
        self.created_at = created_at


def test_build_trend_series_chronological_with_deltas():
    t1 = datetime(2026, 8, 1)
    t2 = datetime(2026, 8, 8)
    t3 = datetime(2026, 8, 15)
    results_desc = [  # newest-first, like the history query
        FakeResult("PHQ-9", 16, "Moderately Severe", t3),
        FakeResult("PHQ-9", 11, "Moderate", t2),
        FakeResult("PHQ-9", 5, "Mild", t1),
    ]
    view = engine.build_trend_series(results_desc)
    assert view["trend"] == "worsened"
    assert [p["delta"] for p in view["points"]] == [None, 6, 5]
    assert view["points"][-1]["severity_band"] == "Moderately Severe"


def test_build_trend_series_single_point():
    view = engine.build_trend_series([FakeResult("GAD-7", 3, "Minimal", datetime(2026, 8, 1))])
    assert view["trend"] == "stable"
    assert len(view["points"]) == 1


def test_build_trend_series_empty():
    view = engine.build_trend_series([])
    assert view["trend"] == "insufficient_data"


# ---------- usage-based smart reminders ----------

def test_reminder_when_no_history():
    r = engine.compute_reminder(None, None)
    assert r["should_remind"] is True
    assert r["reason"] == "no_screening_on_record"


def test_reminder_not_due_default_interval():
    recent = datetime.utcnow() - timedelta(days=3)
    r = engine.compute_reminder(recent, "Minimal")
    assert r["should_remind"] is False
    assert r["reason"] == "not_due"
    assert r["interval_days"] == REMINDER_INTERVAL_DAYS_DEFAULT


def test_reminder_due_default_interval():
    old = datetime.utcnow() - timedelta(days=REMINDER_INTERVAL_DAYS_DEFAULT + 1)
    r = engine.compute_reminder(old, "Minimal")
    assert r["should_remind"] is True
    assert r["reason"] == "interval_elapsed"


def test_reminder_elevated_band_uses_shorter_interval():
    eight_days_ago = datetime.utcnow() - timedelta(days=8)
    r = engine.compute_reminder(eight_days_ago, "Moderate")
    assert r["should_remind"] is True
    assert r["interval_days"] == REMINDER_INTERVAL_DAYS_ELEVATED

    three_days_ago = datetime.utcnow() - timedelta(days=3)
    r2 = engine.compute_reminder(three_days_ago, "Severe")
    assert r2["should_remind"] is False
