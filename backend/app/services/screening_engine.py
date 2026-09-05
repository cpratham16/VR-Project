"""Config-driven screening engine (D2).

Replaces hardcoded PHQ-9/GAD-7 logic with a generic engine that scores any
instrument defined purely by configuration (questions, bands, critical items).
Adding a new validated scale requires only a new ScreeningInstrument row —
no code rebuild.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

BAND_ORDER = ["Minimal", "Mild", "Moderate", "Moderately Severe", "Severe"]

# Usage-based smart reminder rules
REMINDER_INTERVAL_DAYS_DEFAULT = 14          # re-screen at least every 2 weeks
REMINDER_INTERVAL_DAYS_ELEVATED = 7          # sooner when last band was Moderate+
ELEVATED_BANDS = {"Moderate", "Moderately Severe", "Severe"}

class ScreeningEngineService:
    # ---------- validation ----------

    def validate_answers(self, answers: List[int], instrument) -> None:
        """Raise ValueError if answers violate the instrument's config."""
        expected = len(instrument.questions)
        if len(answers) != expected:
            raise ValueError(f"Expected {expected} answers for {instrument.code}")
        for ans in answers:
            if ans < instrument.answer_min or ans > instrument.answer_max:
                raise ValueError(
                    f"Answer scores must be between {instrument.answer_min} and {instrument.answer_max}"
                )

    # ---------- scoring ----------

    def score(self, answers: List[int], instrument) -> Tuple[int, str]:
        """Return (total_score, severity_band) from the instrument's band table.

        Bands are evaluated in listed order; first band whose max_score >= total wins.
        The last band acts as the catch-all.
        """
        total = sum(answers)
        bands = instrument.scoring_bands or []
        for band in bands:
            if total <= band["max_score"]:
                return total, band["label"]
        if bands:
            return total, bands[-1]["label"]
        raise ValueError(f"Instrument {instrument.code} has no scoring_bands configured")

    def check_critical_items(self, answers: List[int], instrument) -> bool:
        """True if any configured critical item scored above answer_min (e.g. PHQ-9 item 9)."""
        critical_ids = set(instrument.critical_items or [])
        if not critical_ids:
            return False
        for q in instrument.questions:
            if q["id"] in critical_ids:
                idx = instrument.questions.index(q)
                if idx < len(answers) and answers[idx] > instrument.answer_min:
                    return True
        return False

    # ---------- trends ----------

    def detect_trend(self, previous_total: int, current_total: int) -> str:
        """Compare two totals of the same instrument. 'worsened' means score increased."""
        if current_total > previous_total:
            return "worsened"
        if current_total < previous_total:
            return "improved"
        return "stable"

    def build_trend_series(self, results_desc: List[Any]) -> Dict[str, Any]:
        """Build patient-facing trend view from results ordered newest-first.

        Returns chronological series (oldest-first) with per-point delta vs
        previous point and an overall trend label for the latest two entries.
        """
        chronological = list(reversed(results_desc))
        series = []
        prev_total: Optional[int] = None
        for r in chronological:
            point = {
                "date": r.created_at.isoformat() if r.created_at else None,
                "total_score": r.total_score,
                "severity_band": r.severity_band,
                "delta": None if prev_total is None else r.total_score - prev_total,
            }
            series.append(point)
            prev_total = r.total_score
        trend = self.detect_trend(chronological[-2].total_score, chronological[-1].total_score) \
            if len(chronological) >= 2 else ("stable" if len(chronological) == 1 else "insufficient_data")
        return {"screening_type": chronological[0].screening_type if chronological else None,
                "trend": trend, "points": series}

    # ---------- usage-based smart reminders ----------

    def compute_reminder(
        self,
        latest_result_time: Optional[datetime],
        latest_severity_band: Optional[str],
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Decide whether to nudge the patient to re-take a screening.

        Rules:
          - No result ever           -> remind (onboarding)
          - Last band elevated       -> remind after REMINDER_INTERVAL_DAYS_ELEVATED days
          - Otherwise                -> remind after REMINDER_INTERVAL_DAYS_DEFAULT days
        """
        now = now or datetime.utcnow()
        if latest_result_time is None:
            return {
                "should_remind": True,
                "reason": "no_screening_on_record",
                "interval_days": REMINDER_INTERVAL_DAYS_DEFAULT,
            }
        interval = timedelta(
            days=REMINDER_INTERVAL_DAYS_ELEVATED
            if latest_severity_band in ELEVATED_BANDS
            else REMINDER_INTERVAL_DAYS_DEFAULT
        )
        due = latest_result_time + interval
        should_remind = now >= due
        return {
            "should_remind": should_remind,
            "reason": "interval_elapsed" if should_remind else "not_due",
            "next_due_at": due.isoformat(),
            "interval_days": interval.days,
        }

screening_engine_service = ScreeningEngineService()
