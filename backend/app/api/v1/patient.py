from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile, ConsentRecord
from app.models.appointment import Appointment
from app.api.deps import get_current_user
from app.schemas.patient import (
    PatientProfileCreate, PatientProfileResponse,
    ConsentRecordCreate, ConsentRecordResponse,
    PatientOnboardingStatus
)
from app.schemas.appointment import AppointmentCreate, AppointmentResponse

router = APIRouter()

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
    db_appt = Appointment(
        patient_id=current_user.id,
        doctor_id=appt_in.doctor_id,
        scheduled_at=appt_in.scheduled_at,
        reason=appt_in.reason,
        status="requested"
    )
    db.add(db_appt)
    await db.commit()
    await db.refresh(db_appt)
    return db_appt

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
    return query.scalars().all()
