import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.patient import PatientProfile, ConsentRecord
from app.models.screening import ScreeningResult
from app.models.mood import MoodEntry
from app.models.appointment import Appointment
from app.models.vr import VRSession
from app.core.security import decrypt_text
from app.api.deps import get_current_user
from app.schemas.patient import (
    PatientProfileCreate, PatientProfileResponse,
    ConsentRecordCreate, ConsentRecordResponse,
    PatientOnboardingStatus
)
from app.schemas.appointment import AppointmentCreate, AppointmentResponse

router = APIRouter()


async def _get_verified_doctor(db: AsyncSession, doctor_id) -> Optional[User]:
    row = (
        await db.execute(
            select(User)
            .outerjoin(DoctorProfile, DoctorProfile.user_id == User.id)
            .where(
                User.id == doctor_id,
                User.role == "doctor",
                User.is_active == True,
                User.is_verified == True,
                DoctorProfile.credential_filename.isnot(None),
            )
        )
    ).scalars().first()
    return row


async def _serialize_appointment(db: AsyncSession, appt: Appointment) -> dict:
    doctor_name = None
    doctor_specialty = None
    doctor_city = None
    doctor_state = None
    if appt.doctor_id:
        drow = (
            await db.execute(select(User).where(User.id == appt.doctor_id))
        ).scalars().first()
        if drow:
            doctor_name = drow.full_name
            doctor_city = drow.city
            doctor_state = drow.state
            prow = (
                await db.execute(
                    select(DoctorProfile).where(DoctorProfile.user_id == appt.doctor_id)
                )
            ).scalars().first()
            if prow:
                doctor_specialty = prow.specialty
    return {
        "id": appt.id,
        "patient_id": appt.patient_id,
        "doctor_id": appt.doctor_id,
        "scheduled_at": appt.scheduled_at,
        "status": appt.status,
        "reason": appt.reason,
        "preferred_mode": appt.preferred_mode,
        "consultation_type": appt.consultation_type,
        "location_notes": appt.location_notes,
        "video_room_url": appt.video_room_url,
        "chat_session_id": appt.chat_session_id,
        "created_at": appt.created_at,
        "updated_at": appt.updated_at,
        "doctor_name": doctor_name,
        "doctor_specialty": doctor_specialty,
        "doctor_city": doctor_city,
        "doctor_state": doctor_state,
    }


@router.get("/doctors")
async def list_available_doctors(
    broaden: bool = Query(False),
    state: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Location-ranked directory of verified doctors (G3, G5).
    Tier 0: same state + same city. Tier 1: same state, other city.
    Out-of-region doctors are hidden unless broaden=true.
    Optional `language` narrows results to doctors listing that language (case-insensitive)."""
    patient_state = (state or current_user.state or "").strip()
    patient_city = (city or current_user.city or "").strip()
    language_filter = (language or "").strip()

    query = (
        select(User, DoctorProfile)
        .outerjoin(DoctorProfile, DoctorProfile.user_id == User.id)
        .where(
            User.role == "doctor",
            User.is_active == True,
            User.is_verified == True,
            DoctorProfile.credential_filename.isnot(None),
        )
    )
    if not broaden and patient_state:
        query = query.where(User.state == patient_state)

    result = await db.execute(query.order_by(User.full_name.asc()))
    rows = result.all()

    doctors = []
    for d, p in rows:
        d_city = (d.city or "").strip().lower()
        d_state = (d.state or "").strip().lower()
        p_city = patient_city.lower()
        p_state = patient_state.lower()

        if p_city and d_city == p_city:
            tier = 0
        elif p_state and d_state == p_state:
            tier = 1
        else:
            tier = 2

        doc_languages = p.languages_list if p else []
        if language_filter:
            spoken = [str(lang).strip().lower() for lang in doc_languages]
            if language_filter.lower() not in spoken:
                continue

        doctors.append({
            "id": str(d.id),
            "full_name": d.full_name,
            "specialty": p.specialty if p else None,
            "languages": doc_languages,
            "city": d.city,
            "state": d.state,
            "_tier": tier,
        })

    doctors.sort(key=lambda x: (x["_tier"], (x["full_name"] or "").lower()))
    return {
        "patient_location": {"city": patient_city or None, "state": patient_state or None},
        "broadened": broaden,
        "language_filter": language_filter or None,
        "doctors": [{k: v for k, v in doc.items() if k != "_tier"} for doc in doctors],
    }

@router.get("/status", response_model=PatientOnboardingStatus)
async def get_onboarding_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile_query = await db.execute(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    has_profile = profile_query.scalars().first() is not None

    consent_query = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == current_user.id)
        .order_by(ConsentRecord.agreed_at.desc())
    )
    latest_consent = consent_query.scalars().first()

    return {
        "has_profile": has_profile,
        "has_consent": latest_consent is not None,
        "latest_consent_version": latest_consent.consent_version if latest_consent else None
    }

@router.post("/profile", response_model=PatientProfileResponse)
async def create_profile(
    profile_in: PatientProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = await db.execute(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Profile already exists")

    db_profile = PatientProfile(
        user_id=current_user.id,
        pseudonym=profile_in.pseudonym
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return db_profile

@router.post("/consent", response_model=ConsentRecordResponse)
async def submit_consent(
    consent_in: ConsentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not consent_in.agreed_to_ai_processing or not consent_in.agreed_to_data_usage:
        raise HTTPException(status_code=400, detail="Must agree to required terms")
        
    db_consent = ConsentRecord(
        user_id=current_user.id,
        consent_version=consent_in.consent_version,
        agreed_to_ai_processing=consent_in.agreed_to_ai_processing,
        agreed_to_data_usage=consent_in.agreed_to_data_usage
    )
    db.add(db_consent)
    await db.commit()
    await db.refresh(db_consent)
    return db_consent

@router.post("/appointments", response_model=AppointmentResponse)
async def request_appointment(
    appt_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if appt_in.doctor_id:
        doctor = await _get_verified_doctor(db, appt_in.doctor_id)
        if not doctor:
            raise HTTPException(
                status_code=400,
                detail="Selected doctor is unavailable. Please choose a verified counselor from the directory."
            )

    db_appt = Appointment(
        patient_id=current_user.id,
        doctor_id=appt_in.doctor_id,
        scheduled_at=appt_in.scheduled_at,
        reason=appt_in.reason,
        preferred_mode=appt_in.preferred_mode or "any",
        status="requested"
    )
    db.add(db_appt)
    await db.commit()
    await db.refresh(db_appt)
    return await _serialize_appointment(db, db_appt)

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_patient_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(Appointment)
        .where(Appointment.patient_id == current_user.id)
        .order_by(Appointment.scheduled_at.desc())
    )
    appts = query.scalars().all()
    return [await _serialize_appointment(db, a) for a in appts]

@router.get("/appointments/{appointment_id}/ical")
async def download_appointment_ical(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download standard iCalendar (.ics) event file for Google/Outlook/Apple Calendar (D4)."""
    query = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == current_user.id
        )
    )
    appt = query.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    location_url = appt.video_room_url or appt.location_notes or "Online Consultation"
    summary = f"Mental Health Appointment ({appt.consultation_type or appt.preferred_mode})"
    description = f"Reason: {appt.reason or 'Consultation'}\\nStatus: {appt.status}"

    start_str = appt.scheduled_at.strftime("%Y%m%dT%H%M%SZ")
    end_str = (appt.scheduled_at + timedelta(hours=1)).strftime("%Y%m%dT%H%M%SZ")
    now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    ical_text = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Mindora Mental Health Platform//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:REQUEST\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:appt-{appt.id}@mindora.health\r\n"
        f"DTSTAMP:{now_str}\r\n"
        f"DTSTART:{start_str}\r\n"
        f"DTEND:{end_str}\r\n"
        f"SUMMARY:{summary}\r\n"
        f"DESCRIPTION:{description}\r\n"
        f"LOCATION:{location_url}\r\n"
        "STATUS:CONFIRMED\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR"
    )

    return Response(
        content=ical_text,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=appointment-{appt.id}.ics"}
    )

@router.get("/export")
async def export_patient_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Patient data export endpoint (D3c / GDPR / DPDP Act 2023 compliance).
    Generates a full JSON payload of all patient records (decrypted).
    """
    prof_q = await db.execute(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    profile = prof_q.scalars().first()

    consent_q = await db.execute(select(ConsentRecord).where(ConsentRecord.user_id == current_user.id))
    consents = consent_q.scalars().all()

    screening_q = await db.execute(select(ScreeningResult).where(ScreeningResult.user_id == current_user.id))
    screenings = screening_q.scalars().all()

    mood_q = await db.execute(select(MoodEntry).where(MoodEntry.user_id == current_user.id))
    moods = mood_q.scalars().all()

    appt_q = await db.execute(select(Appointment).where(Appointment.patient_id == current_user.id))
    appts = appt_q.scalars().all()

    vr_q = await db.execute(select(VRSession).where(VRSession.patient_id == current_user.id))
    vr_sessions = vr_q.scalars().all()

    return {
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "user_id": str(current_user.id),
            "email": current_user.email,
        },
        "user_profile": {
            "role": current_user.role,
            "state": current_user.state,
            "city": current_user.city,
            "pseudonym": profile.pseudonym if profile else None,
        },
        "consents": [
            {
                "version": c.consent_version,
                "ai_processing": c.agreed_to_ai_processing,
                "data_usage": c.agreed_to_data_usage,
                "agreed_at": c.agreed_at.isoformat() if c.agreed_at else None,
            }
            for c in consents
        ],
        "screenings": [
            {
                "type": s.screening_type,
                "score": s.total_score,
                "severity_band": s.severity_band,
                "answers": s.answers,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in screenings
        ],
        "mood_history": [
            {
                "mood_score": m.mood_score,
                "tags": m.tags,
                "journal_text": decrypt_text(m.journal_text) if m.journal_text else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in moods
        ],
        "appointments": [
            {
                "status": a.status,
                "scheduled_at": a.scheduled_at.isoformat() if a.scheduled_at else None,
                "reason": a.reason,
            }
            for a in appts
        ],
        "vr_sessions": [
            {
                "status": v.status,
                "intensity_level": v.intensity_level,
                "suds_pre": v.suds_pre,
                "suds_post": v.suds_post,
                "patient_feedback": v.patient_feedback,
                "assigned_at": v.assigned_at.isoformat() if v.assigned_at else None,
            }
            for v in vr_sessions
        ],
    }
