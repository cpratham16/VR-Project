"""Anonymization ETL pipeline.

Reads clinical/activity tables, groups by (region, YYYY-MM), computes numeric
aggregates only, and writes them into the identifier-free reporting store
(RegionalAggregate). This is a one-way boundary: aggregates can never be
resolved back to an individual because no identifiers are persisted here.
"""
from datetime import datetime
from collections import defaultdict
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.screening import ScreeningResult
from app.models.mood import MoodEntry
from app.models.alert import RiskAlert
from app.models.vr import VRSession
from app.models.anonymized import RegionalAggregate

DEFAULT_REGION = "Unknown Region"


def resolve_region(user: User) -> str:
    if user.city and user.state:
        return f"{user.city}, {user.state}"
    if user.state:
        return user.state
    if user.city:
        return user.city
    return DEFAULT_REGION


def _period_key(ts: datetime | None) -> str:
    if not ts:
        return datetime.utcnow().strftime("%Y-%m")
    return ts.strftime("%Y-%m")


async def run_aggregation(db: AsyncSession) -> dict:
    """Aggregate clinical data into the anonymized reporting store.

    Returns a summary dict of rows written / totals for admin feedback.
    """
    # Load users (only need id -> region)
    users_q = await db.execute(select(User))
    users = users_q.scalars().all()
    region_by_user = {u.id: resolve_region(u) for u in users}
    patient_ids = {u.id for u in users if u.role == "patient"}

    # patients with screening/mood/alert activity (excluding unknown region)
    active_patients = {
        uid for uid, reg in region_by_user.items()
        if uid in patient_ids and reg != DEFAULT_REGION
    }

    # bucket structures
    buckets = defaultdict(lambda: {
        "region": "",
        "period": "",
        "total_patients": set(),
        "screening_count": 0,
        "phq9": defaultdict(int),
        "gad7": defaultdict(int),
        "mood_sum": 0.0,
        "mood_count": 0,
        "risk_alert_count": 0,
        "vr_sessions_completed": 0,
    })

    def bucket(region: str, period: str):
        key = (region, period)
        if key not in buckets:
            buckets[key]["region"] = region
            buckets[key]["period"] = period
        return buckets[key]

    # Screenings
    screenings_q = await db.execute(select(ScreeningResult))
    for s in screenings_q.scalars().all():
        region = region_by_user.get(s.user_id)
        if not region or region == DEFAULT_REGION:
            continue
        b = bucket(region, _period_key(s.created_at))
        b["screening_count"] += 1
        b["total_patients"].add(s.user_id)
        if s.screening_type == "PHQ-9":
            b["phq9"][s.severity_band] += 1
        elif s.screening_type == "GAD-7":
            b["gad7"][s.severity_band] += 1

    # Mood entries
    moods_q = await db.execute(select(MoodEntry))
    for m in moods_q.scalars().all():
        region = region_by_user.get(m.user_id)
        if not region or region == DEFAULT_REGION:
            continue
        b = bucket(region, _period_key(m.created_at))
        b["mood_sum"] += float(m.mood_score)
        b["mood_count"] += 1
        b["total_patients"].add(m.user_id)

    # Risk alerts (CRITICAL + HIGH only)
    alerts_q = await db.execute(select(RiskAlert))
    for a in alerts_q.scalars().all():
        region = region_by_user.get(a.user_id)
        if not region or region == DEFAULT_REGION:
            continue
        if a.severity in ("CRITICAL", "HIGH"):
            b = bucket(region, _period_key(a.created_at))
            b["risk_alert_count"] += 1
            b["total_patients"].add(a.user_id)

    # Completed VR sessions
    vr_q = await db.execute(select(VRSession))
    for v in vr_q.scalars().all():
        if v.status != "completed":
            continue
        region = region_by_user.get(v.patient_id)
        if not region or region == DEFAULT_REGION:
            continue
        b = bucket(region, _period_key(v.completed_at))
        b["vr_sessions_completed"] += 1
        b["total_patients"].add(v.patient_id)

    # Upsert: delete existing rows for each (region, period), insert fresh
    total_rows = 0
    for key, b in buckets.items():
        region, period = key
        await db.execute(
            delete(RegionalAggregate).where(
                RegionalAggregate.region == region,
                RegionalAggregate.period == period,
            )
        )
        avg_mood = (b["mood_sum"] / b["mood_count"]) if b["mood_count"] else 0.0
        row = RegionalAggregate(
            region=region,
            period=period,
            total_patients=len(b["total_patients"]),
            screening_count=b["screening_count"],
            phq9_minimal=b["phq9"].get("Minimal", 0),
            phq9_mild=b["phq9"].get("Mild", 0),
            phq9_moderate=b["phq9"].get("Moderate", 0),
            phq9_moderately_severe=b["phq9"].get("Moderately Severe", 0),
            phq9_severe=b["phq9"].get("Severe", 0),
            gad7_minimal=b["gad7"].get("Minimal", 0),
            gad7_mild=b["gad7"].get("Mild", 0),
            gad7_moderate=b["gad7"].get("Moderate", 0),
            gad7_severe=b["gad7"].get("Severe", 0),
            avg_mood_score=round(avg_mood, 2),
            mood_entry_count=b["mood_count"],
            risk_alert_count=b["risk_alert_count"],
            vr_sessions_completed=b["vr_sessions_completed"],
        )
        db.add(row)
        total_rows += 1

    await db.commit()

    return {
        "rows_written": total_rows,
        "regions": len(buckets),
        "active_patients": len(active_patients),
        "screening_count": sum(b["screening_count"] for b in buckets.values()),
        "risk_alert_count": sum(b["risk_alert_count"] for b in buckets.values()),
        "vr_sessions_completed": sum(b["vr_sessions_completed"] for b in buckets.values()),
    }
