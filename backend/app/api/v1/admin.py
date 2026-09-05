import csv
import io
import os
import uuid
from datetime import datetime
from typing import List, Optional
from statistics import mean, pstdev
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.anonymized import RegionalAggregate
from app.models.screening_instrument import ScreeningInstrument
from app.api.deps import get_current_admin
from app.api.v1.auth import _serialize_user
from app.schemas.user import AdminCreate, UserResponse
from app.services.anonymizer import run_aggregation
from pydantic import BaseModel

router = APIRouter()

MIN_SUPPRESSION_THRESHOLD = 10


@router.get("/doctors/{user_id}/credential", response_class=FileResponse)
async def download_doctor_credential(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    try:
        doctor_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    profile = (
        await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == doctor_uuid))
    ).scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    if not profile.credential_path or not os.path.exists(profile.credential_path):
        raise HTTPException(status_code=404, detail="No credential document on file")
    return FileResponse(
        profile.credential_path,
        filename=profile.credential_filename or "credential",
    )


@router.get("/doctors")
async def list_doctors_for_review(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(User).where(User.role == "doctor").order_by(User.created_at.asc())
    )
    doctors = result.scalars().all()
    out = []
    for d in doctors:
        profile = (
            await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == d.id))
        ).scalars().first()
        review_status = profile.review_status if profile else None
        if status_filter and review_status != status_filter:
            continue
        out.append({
            "user_id": d.id,
            "email": d.email,
            "full_name": d.full_name,
            "state": d.state,
            "city": d.city,
            "is_verified": d.is_verified,
            "has_credentials": bool(profile and profile.credential_filename),
            "license_number": profile.license_number if profile else None,
            "specialty": profile.specialty if profile else None,
            "languages": profile.languages_list if profile else [],
            "review_status": review_status or ("approved" if d.is_verified else "pending"),
            "rejection_reason": profile.rejection_reason if profile else None,
            "uploaded_at": profile.uploaded_at if profile else None,
        })
    return out


class DoctorReviewAction(BaseModel):
    reason: Optional[str] = None


async def _get_doctor_with_profile(db: AsyncSession, user_id: str):
    try:
        doctor_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor = (
        await db.execute(select(User).where(User.id == doctor_uuid, User.role == "doctor"))
    ).scalars().first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    profile = (
        await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == doctor_uuid))
    ).scalars().first()
    return doctor, profile


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_admin_user(
    user_in: AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Provision a new administrator account. Only admins can create admins."""
    existing = (
        await db.execute(select(User).where(User.email == user_in.email))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role="admin",
        state=user_in.state,
        city=user_in.city,
        full_name=user_in.full_name,
        is_verified=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return await _serialize_user(db, db_user)


@router.post("/doctors/{user_id}/approve")
async def approve_doctor(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    doctor, profile = await _get_doctor_with_profile(db, user_id)
    if not profile or not profile.credential_filename:
        raise HTTPException(status_code=400, detail="Doctor has no credential document on file to review")

    doctor.is_verified = True
    profile.review_status = "approved"
    profile.rejection_reason = None
    profile.reviewed_by_admin_id = current_admin.id
    profile.reviewed_at = datetime.utcnow()
    await db.commit()
    return {
        "message": f"{doctor.email} approved",
        "user_id": str(doctor.id),
        "review_status": "approved",
        "reviewed_at": profile.reviewed_at,
    }


@router.post("/doctors/{user_id}/reject")
async def reject_doctor(
    user_id: str,
    action: DoctorReviewAction,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if not action.reason or not action.reason.strip():
        raise HTTPException(status_code=400, detail="A rejection reason is required")

    doctor, profile = await _get_doctor_with_profile(db, user_id)

    doctor.is_verified = False
    if profile:
        profile.review_status = "rejected"
        profile.rejection_reason = action.reason.strip()
        profile.reviewed_by_admin_id = current_admin.id
        profile.reviewed_at = datetime.utcnow()
    else:
        profile = DoctorProfile(
            user_id=doctor.id,
            license_number="UNKNOWN",
            languages="[]",
            review_status="rejected",
            rejection_reason=action.reason.strip(),
            reviewed_by_admin_id=current_admin.id,
            reviewed_at=datetime.utcnow(),
        )
        db.add(profile)
    await db.commit()
    return {
        "message": f"{doctor.email} rejected",
        "user_id": str(doctor.id),
        "review_status": "rejected",
        "rejection_reason": action.reason.strip(),
    }


def check_admin_jurisdiction(admin: User, target_region: Optional[str] = None) -> Optional[str]:
    """
    Enforces role-scoped data-access layer restrictions.
    If an admin has a designated state (e.g. 'California'), they are strictly prohibited from
    querying data outside their jurisdiction. Aggregate region keys are 'City, State' (or just
    'State'), so a target region is allowed when it equals the admin's state or carries it as a
    suffix (e.g. 'San Francisco, California').
    """
    if admin.state and admin.state.upper() not in ["ALL", "GLOBAL", ""]:
        admin_jurisdiction = admin.state.strip()
        if target_region:
            target = target_region.strip().lower()
            allowed = (
                target == admin_jurisdiction.lower()
                or target.endswith(f", {admin_jurisdiction.lower()}")
            )
            if not allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied: State-level admin jurisdiction is restricted to '{admin_jurisdiction}'."
                )
        return admin_jurisdiction
    return target_region


def _jurisdiction_filter(region_key: Optional[str]):
    """SQLAlchemy condition matching a state-scoped admin's region(s).

    Aggregate region keys are '{city}, {state}' (or bare '{state}'), so a jurisdiction
    filter matches the exact state and any region carrying it as a suffix.
    """
    if not region_key:
        return True
    return or_(
        RegionalAggregate.region == region_key,
        RegionalAggregate.region.ilike(f"%, {region_key}"),
    )


def _period_desc(a: RegionalAggregate, min_threshold: int = MIN_SUPPRESSION_THRESHOLD) -> dict:
    is_suppressed = a.total_patients < min_threshold
    if is_suppressed:
        return {
            "region": a.region,
            "period": a.period,
            "total_patients": "insufficient_data (<10)",
            "suppressed": True,
            "screening_count": None,
            "phq9_minimal": None,
            "phq9_mild": None,
            "phq9_moderate": None,
            "phq9_moderately_severe": None,
            "phq9_severe": None,
            "gad7_minimal": None,
            "gad7_mild": None,
            "gad7_moderate": None,
            "gad7_severe": None,
            "avg_mood_score": None,
            "mood_entry_count": None,
            "risk_alert_count": None,
            "vr_sessions_completed": None,
        }
    return {
        "region": a.region,
        "period": a.period,
        "total_patients": a.total_patients,
        "suppressed": False,
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


class InstrumentUpsert(BaseModel):
    code: str
    title: str
    instructions: str
    options: list
    questions: list
    scoring_bands: list  # [{"max_score": int, "label": str}, ...] ascending
    answer_min: int = 0
    answer_max: int = 3
    critical_items: Optional[list] = None
    is_active: bool = True


@router.get("/screening/instruments")
async def list_screening_instruments(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(ScreeningInstrument).order_by(ScreeningInstrument.code))
    return [
        {
            "code": i.code,
            "title": i.title,
            "instructions": i.instructions,
            "options": i.options,
            "questions": i.questions,
            "scoring_bands": i.scoring_bands,
            "answer_min": i.answer_min,
            "answer_max": i.answer_max,
            "critical_items": i.critical_items or [],
            "is_active": i.is_active,
        }
        for i in result.scalars().all()
    ]


@router.post("/screening/instruments")
async def upsert_screening_instrument(
    instrument_in: InstrumentUpsert,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Create or update a screening scale purely via configuration (D2 acceptance:
    a new validated scale is added via config, not a code rebuild)."""
    if not instrument_in.questions:
        raise HTTPException(status_code=400, detail="questions must not be empty")
    if not instrument_in.scoring_bands:
        raise HTTPException(status_code=400, detail="scoring_bands must not be empty")
    maxes = [b["max_score"] for b in instrument_in.scoring_bands]
    if any(b < 0 for b in maxes) or maxes != sorted(maxes):
        raise HTTPException(status_code=400, detail="scoring_bands max_score values must ascend")

    existing = (
        await db.execute(select(ScreeningInstrument).where(ScreeningInstrument.code == instrument_in.code))
    ).scalars().first()
    data = instrument_in.model_dump()
    if existing:
        for key, value in data.items():
            setattr(existing, key, value)
        target = existing
    else:
        target = ScreeningInstrument(**data)
        db.add(target)
    await db.commit()
    await db.refresh(target)
    return {"message": f"Instrument {target.code} saved", "code": target.code}


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
    allowed_region = check_admin_jurisdiction(current_admin)
    query = select(RegionalAggregate)
    if allowed_region:
        query = query.where(_jurisdiction_filter(allowed_region))

    result = await db.execute(query)
    rows = result.scalars().all()

    total_patients_sum = sum(r.total_patients for r in rows)
    if total_patients_sum < MIN_SUPPRESSION_THRESHOLD:
        return {
            "total_patients": "insufficient_data (<10)",
            "suppressed": True,
            "screening_count": None,
            "risk_alert_count": None,
            "vr_sessions_completed": None,
            "mood_entry_count": None,
            "phq9_bands": None,
            "gad7_bands": None,
            "regions_covered": len({r.region for r in rows}),
        }

    overview = {
        "total_patients": 0,
        "suppressed": False,
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
    allowed_region = check_admin_jurisdiction(current_admin)
    query = select(RegionalAggregate.region).distinct()
    if allowed_region:
        query = query.where(_jurisdiction_filter(allowed_region))
    result = await db.execute(query.order_by(RegionalAggregate.region))
    return [r[0] for r in result.all()]


@router.get("/analytics/trend")
async def get_trend(
    region: Optional[str] = Query(None),
    months: int = 12,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    effective_region = check_admin_jurisdiction(current_admin, target_region=region)
    query = select(RegionalAggregate)
    if effective_region:
        query = query.where(_jurisdiction_filter(effective_region))
    result = await db.execute(query.order_by(RegionalAggregate.period.asc()))
    rows = result.scalars().all()

    m_val = int(months) if isinstance(months, int) else 12
    if len(rows) > m_val:
        periods = sorted({r.period for r in rows})
        cutoff = periods[-m_val:]
        rows = [r for r in rows if r.period in cutoff]

    return [_period_desc(r) for r in rows]


@router.get("/analytics/spikes")
async def get_spikes(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    allowed_region = check_admin_jurisdiction(current_admin)
    query = select(RegionalAggregate)
    if allowed_region:
        query = query.where(_jurisdiction_filter(allowed_region))
    result = await db.execute(query)
    rows = result.scalars().all()

    by_region: dict[str, list] = {}
    for r in rows:
        if r.total_patients < MIN_SUPPRESSION_THRESHOLD:
            continue  # Suppress small cohorts from spike analysis
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


@router.get("/analytics/export")
async def export_analytics(
    format: str = Query("csv"),
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    effective_region = check_admin_jurisdiction(current_admin, target_region=region)
    query = select(RegionalAggregate)
    if effective_region:
        query = query.where(_jurisdiction_filter(effective_region))
    result = await db.execute(query.order_by(RegionalAggregate.period.asc()))
    rows = result.scalars().all()

    described_rows = [_period_desc(r) for r in rows]

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "region", "period", "total_patients", "suppressed",
            "screening_count", "risk_alert_count", "vr_sessions_completed", "avg_mood_score"
        ])
        for row in described_rows:
            writer.writerow([
                row["region"],
                row["period"],
                row["total_patients"],
                row["suppressed"],
                row["screening_count"],
                row["risk_alert_count"],
                row["vr_sessions_completed"],
                row["avg_mood_score"]
            ])
        csv_bytes = output.getvalue().encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="regional_analytics.csv"'}
        )

    # Basic PDF generation format
    pdf_lines = [
        "%PDF-1.4",
        "1 0 obj < /Type /Catalog /Pages 2 0 R > endobj",
        "2 0 obj < /Type /Pages /Kids [3 0 R] /Count 1 > endobj",
        "3 0 obj < /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R > endobj",
        "4 0 obj < /Length 200 > stream",
        "BT /F1 12 Tf 50 750 Td (Mental Health Platform - Admin Analytics Export) Tj ET",
    ]
    for idx, row in enumerate(described_rows[:20]):
        line_str = f"({row['region']} | {row['period']} | Patients: {row['total_patients']}) Tj"
        pdf_lines.append(f"BT /F1 10 Tf 50 {720 - idx * 20} Td {line_str} ET")
    pdf_lines.extend(["endstream endobj", "xref", "0 5", "trailer < /Root 1 0 R >", "%%EOF"])
    pdf_bytes = "\n".join(pdf_lines).encode("utf-8")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="regional_analytics.pdf"'}
    )
