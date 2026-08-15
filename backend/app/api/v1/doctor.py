from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.screening import ScreeningResult
from app.models.mood import MoodEntry
from app.models.note import ClinicalNote
from app.models.appointment import Appointment
from app.api.deps import get_current_doctor
from app.schemas.doctor import TriagePatient, PatientDetailResponse, DoctorVerifyResponse
from app.schemas.note import ClinicalNoteCreate, ClinicalNoteResponse
from app.schemas.appointment import AppointmentStatusUpdate, AppointmentResponse

router = APIRouter()

@router.get("/triage", response_model=List[TriagePatient])
async def get_triage_patients(
    severity_filter: Optional[str] = Query(None, description="Filter by risk level: High, Moderate, Low, Unassessed"),
    sort_by: str = Query("risk", description="Sort by: 'risk' or 'recency'"),
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    # Fetch all patients
    patient_query = await db.execute(select(User).where(User.role == "patient"))
    patients = patient_query.scalars().all()
    
    triage_list: List[TriagePatient] = []
    
    for p in patients:
        # Fetch profile
        prof_q = await db.execute(select(PatientProfile).where(PatientProfile.user_id == p.id))
        prof = prof_q.scalars().first()
        
        # Fetch latest PHQ-9
        phq_q = await db.execute(
            select(ScreeningResult)
            .where(ScreeningResult.user_id == p.id, ScreeningResult.screening_type == "PHQ-9")
            .order_by(ScreeningResult.created_at.desc())
        )
        latest_phq = phq_q.scalars().first()
        
        # Fetch latest GAD-7
        gad_q = await db.execute(
            select(ScreeningResult)
            .where(ScreeningResult.user_id == p.id, ScreeningResult.screening_type == "GAD-7")
            .order_by(ScreeningResult.created_at.desc())
        )
        latest_gad = gad_q.scalars().first()
        
        # Fetch latest Mood
        mood_q = await db.execute(
            select(MoodEntry)
            .where(MoodEntry.user_id == p.id)
            .order_by(MoodEntry.created_at.desc())
        )
        latest_mood = mood_q.scalars().first()
        
        # Determine risk level
        phq_sev = latest_phq.severity_band if latest_phq else None
        gad_sev = latest_gad.severity_band if latest_gad else None
        mood_score = latest_mood.mood_score if latest_mood else None
        
        is_high = (
            phq_sev in ["Severe", "Moderately Severe"] or
            gad_sev == "Severe" or
            (mood_score is not None and mood_score == 1)
        )
        is_mod = (
            phq_sev == "Moderate" or
            gad_sev == "Moderate" or
            (mood_score is not None and mood_score == 2)
        )
        
        has_any = (latest_phq is not None or latest_gad is not None or latest_mood is not None)
        
        if is_high:
            risk_level = "High"
            risk_num = 3
        elif is_mod:
            risk_level = "Moderate"
            risk_num = 2
        elif has_any:
            risk_level = "Low"
            risk_num = 1
        else:
            risk_level = "Unassessed"
            risk_num = 0
            
        # Calculate last activity
        activity_dates = [p.created_at]
        if latest_phq: activity_dates.append(latest_phq.created_at)
        if latest_gad: activity_dates.append(latest_gad.created_at)
        if latest_mood: activity_dates.append(latest_mood.created_at)
        last_active = max(activity_dates)
        
        item = TriagePatient(
            user_id=p.id,
            email=p.email,
            pseudonym=prof.pseudonym if prof else None,
            latest_phq9_score=latest_phq.total_score if latest_phq else None,
            latest_phq9_severity=phq_sev,
            latest_gad7_score=latest_gad.total_score if latest_gad else None,
            latest_gad7_severity=gad_sev,
            latest_mood_score=mood_score,
            last_activity=last_active,
            risk_level=risk_level,
            risk_numeric=risk_num
        )
        
        if severity_filter:
            if item.risk_level.lower() == severity_filter.lower():
                triage_list.append(item)
        else:
            triage_list.append(item)
            
    # Sorting
    if sort_by == "recency":
        triage_list.sort(key=lambda x: x.last_activity or datetime.min, reverse=True)
    else: # default "risk"
        triage_list.sort(key=lambda x: (x.risk_numeric, x.last_activity or datetime.min), reverse=True)
        
    return triage_list

@router.post("/verify-self", response_model=DoctorVerifyResponse)
async def verify_self_doctor(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    current_doctor.is_verified = True
    await db.commit()
    await db.refresh(current_doctor)
    return current_doctor

@router.get("/patient/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_detail(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    patient_q = await db.execute(select(User).where(User.id == patient_id, User.role == "patient"))
    patient = patient_q.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    prof_q = await db.execute(select(PatientProfile).where(PatientProfile.user_id == patient_id))
    prof = prof_q.scalars().first()

    scr_q = await db.execute(
        select(ScreeningResult)
        .where(ScreeningResult.user_id == patient_id)
        .order_by(ScreeningResult.created_at.desc())
    )
    screenings = scr_q.scalars().all()

    mood_q = await db.execute(
        select(MoodEntry)
        .where(MoodEntry.user_id == patient_id)
        .order_by(MoodEntry.created_at.desc())
    )
    mood_entries = mood_q.scalars().all()
    
    notes_q = await db.execute(
        select(ClinicalNote)
        .where(ClinicalNote.patient_id == patient_id)
        .order_by(ClinicalNote.created_at.desc())
    )
    notes = notes_q.scalars().all()

    # Determine risk level
    latest_phq = next((s for s in screenings if s.screening_type == "PHQ-9"), None)
    latest_gad = next((s for s in screenings if s.screening_type == "GAD-7"), None)
    latest_mood = mood_entries[0] if mood_entries else None

    phq_sev = latest_phq.severity_band if latest_phq else None
    gad_sev = latest_gad.severity_band if latest_gad else None
    m_score = latest_mood.mood_score if latest_mood else None

    if (phq_sev in ["Severe", "Moderately Severe"] or gad_sev == "Severe" or m_score == 1):
        risk = "High"
    elif (phq_sev == "Moderate" or gad_sev == "Moderate" or m_score == 2):
        risk = "Moderate"
    elif (screenings or mood_entries):
        risk = "Low"
    else:
        risk = "Unassessed"

    # Map mood entries with can_edit flag
    from app.schemas.mood import MoodEntryResponse
    mapped_moods = []
    for m in mood_entries:
        item = MoodEntryResponse.model_validate(m)
        item.can_edit = False
        mapped_moods.append(item)

    return PatientDetailResponse(
        user_id=patient.id,
        email=patient.email,
        pseudonym=prof.pseudonym if prof else None,
        risk_level=risk,
        screenings=screenings,
        mood_entries=mapped_moods,
        clinical_notes=notes
    )

@router.post("/patient/{patient_id}/notes", response_model=ClinicalNoteResponse)
async def create_clinical_note(
    patient_id: str,
    note_in: ClinicalNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    patient_q = await db.execute(select(User).where(User.id == patient_id, User.role == "patient"))
    if not patient_q.scalars().first():
        raise HTTPException(status_code=404, detail="Patient not found")

    db_note = ClinicalNote(
        patient_id=patient_id,
        doctor_id=current_doctor.id,
        note_text=note_in.note_text
    )
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_doctor_appointments(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    query = await db.execute(
        select(Appointment)
        .order_by(Appointment.scheduled_at.asc())
    )
    appts = query.scalars().all()
    
    results = []
    for a in appts:
        # Fetch patient email & pseudonym
        p_query = await db.execute(select(User).where(User.id == a.patient_id))
        patient = p_query.scalars().first()
        prof_query = await db.execute(select(PatientProfile).where(PatientProfile.user_id == a.patient_id))
        prof = prof_query.scalars().first()
        
        item = AppointmentResponse.model_validate(a)
        if patient:
            item.patient_email = patient.email
        if prof:
            item.patient_pseudonym = prof.pseudonym
        results.append(item)
        
    return results

@router.put("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: str,
    status_in: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    query = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = query.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if status_in.status not in ["requested", "confirmed", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    appt.status = status_in.status
    appt.doctor_id = current_doctor.id
    appt.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(appt)
    
    item = AppointmentResponse.model_validate(appt)
    p_query = await db.execute(select(User).where(User.id == appt.patient_id))
    patient = p_query.scalars().first()
    prof_query = await db.execute(select(PatientProfile).where(PatientProfile.user_id == appt.patient_id))
    prof = prof_query.scalars().first()
    if patient: item.patient_email = patient.email
    if prof: item.patient_pseudonym = prof.pseudonym
    return item
