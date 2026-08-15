from typing import List, Optional
from statistics import mean, pstdev
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.anonymized import RegionalAggregate
from app.api.deps import get_current_admin
from app.services.anonymizer import run_aggregation

router = APIRouter()

def _period_desc(a: RegionalAggregate) -> dict:
    return {
        "region": a.region,
        "period": a.period,
        "total_patients": a.total_patients,
        "screening_count": a.screening_count,
        "phq9_minimal": a.phq9_minimal,
        "phq9_mild": a.phq9_mild,
        "phq9_moderate": a.phq9_moderate,
        "phq9_moderately_severe": a.phq9_moderately_severe,
        "phq9_severe": a.phq9_severe,
        "gad7_minimal": a.gad7_minimal,
        "gad7_mild": a.gad7_mild,
        "gad7_moderate": a.gad7_moderate,
        "gad7_severe": a.gad7_severe,
        "avg_mood_score": a.avg_mood_score,
        "mood_entry_count": a.mood_entry_count,
        "risk_alert_count": a.risk_alert_count,
        "vr_sessions_completed": a.vr_sessions_completed,
    }

@router.post("/analytics/run-pipeline")
async def trigger_pipeline(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await run_aggregation(db)
    return {"message": "Anonymization pipeline completed", **result}

@router.get("/analytics/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(RegionalAggregate))
    rows = result.scalars().all()

    overview = {
        "total_patients": 0,
        "screening_count": 0,
        "risk_alert_count": 0,
        "vr_sessions_completed": 0,
        "mood_entry_count": 0,
        "phq9_bands": {
            "Minimal": 0, "Mild": 0, "Moderate": 0,
            "Moderately Severe": 0, "Severe": 0,
        },
        "gad7_bands": {
            "Minimal": 0, "Mild": 0, "Moderate": 0, "Severe": 0,
        },
        "regions_covered": len({r.region for r in rows}),
    }

    for r in rows:
        overview["total_patients"] += r.total_patients
        overview["screening_count"] += r.screening_count
        overview["risk_alert_count"] += r.risk_alert_count
        overview["vr_sessions_completed"] += r.vr_sessions_completed
        overview["mood_entry_count"] += r.mood_entry_count
        overview["phq9_bands"]["Minimal"] += r.phq9_minimal
        overview["phq9_bands"]["Mild"] += r.phq9_mild
        overview["phq9_bands"]["Moderate"] += r.phq9_moderate
        overview["phq9_bands"]["Moderately Severe"] += r.phq9_moderately_severe
        overview["phq9_bands"]["Severe"] += r.phq9_severe
        overview["gad7_bands"]["Minimal"] += r.gad7_minimal
        overview["gad7_bands"]["Mild"] += r.gad7_mild
        overview["gad7_bands"]["Moderate"] += r.gad7_moderate
        overview["gad7_bands"]["Severe"] += r.gad7_severe

    return overview

@router.get("/analytics/regions")
async def list_regions(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(RegionalAggregate.region).distinct().order_by(RegionalAggregate.region))
    return [r[0] for r in result.all()]

@router.get("/analytics/trend")
async def get_trend(
    region: Optional[str] = Query(None),
    months: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    query = select(RegionalAggregate)
    if region:
        query = query.where(RegionalAggregate.region == region)
    result = await db.execute(query.order_by(RegionalAggregate.period.asc()))
    rows = result.scalars().all()

    # Keep only the most recent `months` periods overall
    if len(rows) > months:
        periods = sorted({r.period for r in rows})
        cutoff = periods[-months:]
        rows = [r for r in rows if r.period in cutoff]

    return [_period_desc(r) for r in rows]

@router.get("/analytics/spikes")
async def get_spikes(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Flag region+period where alert rate per patient exceeds mean + 2σ of
    that region's history."""
    result = await db.execute(select(RegionalAggregate))
    rows = result.scalars().all()

    by_region: dict[str, list] = {}
    for r in rows:
        rate = r.risk_alert_count / r.total_patients if r.total_patients else 0.0
        by_region.setdefault(r.region, []).append((r, rate))

    spikes = []
    for region, entries in by_region.items():
        rates = [e[1] for e in entries]
        if len(rates) < 2:
            continue
        mu = mean(rates)
        sigma = pstdev(rates)
        threshold = mu + 2 * sigma
        for r, rate in entries:
            if sigma > 0 and rate > threshold and rate > 0.05:
                spikes.append({
                    "region": region,
                    "period": r.period,
                    "alert_rate": round(rate, 3),
                    "alert_count": r.risk_alert_count,
                    "patients": r.total_patients,
                    "threshold": round(threshold, 3),
                })

    spikes.sort(key=lambda s: s["alert_rate"], reverse=True)
    return spikes
