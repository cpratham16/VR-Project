from typing import List, Optional
from datetime import datetime, timedelta
from statistics import mean, pstdev
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.screening import ScreeningResult
from app.models.mood import MoodEntry
from app.models.note import ClinicalNote
from app.models.appointment import Appointment
from app.models.chat import ChatSession, ChatMessage
from app.api.deps import get_current_doctor, get_current_verified_doctor
from app.schemas.doctor import TriagePatient, PatientDetailResponse
from app.schemas.note import ClinicalNoteCreate, ClinicalNoteUpdate, ClinicalNoteResponse
from app.schemas.appointment import AppointmentStatusUpdate, AppointmentResponse, AppointmentTriageRequest

router = APIRouter()

@router.get("/triage", response_model=List[TriagePatient])
async def get_triage_patients(
    severity_filter: Optional[str] = Query(None, description="Filter by risk level: High, Moderate, Low, Unassessed"),
    sort_by: str = Query("risk", description="Sort by: 'risk' or 'recency'"),
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
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

@router.post("/verify-self", include_in_schema=False)
async def verify_self_doctor_removed():
    raise HTTPException(
        status_code=http_status.HTTP_403_FORBIDDEN,
        detail="Doctor verification is performed exclusively by administrators",
    )

@router.get("/patient/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_detail(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
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
    current_doctor: User = Depends(get_current_verified_doctor)
):
    patient_q = await db.execute(select(User).where(User.id == patient_id, User.role == "patient"))
    if not patient_q.scalars().first():
        raise HTTPException(status_code=404, detail="Patient not found")

    fmt_type = (note_in.format_type or "free_text").upper()
    if fmt_type == "SOAP":
        note_text = note_in.note_text or (
            f"Subjective: {note_in.soap_subjective or 'N/A'}\n"
            f"Objective: {note_in.soap_objective or 'N/A'}\n"
            f"Assessment: {note_in.soap_assessment or 'N/A'}\n"
            f"Plan: {note_in.soap_plan or 'N/A'}"
        )
    else:
        note_text = note_in.note_text or "Clinical Note"

    db_note = ClinicalNote(
        patient_id=patient_id,
        doctor_id=current_doctor.id,
        note_text=note_text,
        version=1,
        is_latest=True,
        format_type=fmt_type,
        soap_subjective=note_in.soap_subjective,
        soap_objective=note_in.soap_objective,
        soap_assessment=note_in.soap_assessment,
        soap_plan=note_in.soap_plan
    )
    db.add(db_note)
    await db.commit()
    await db.refresh(db_note)
    return db_note

@router.put("/notes/{note_id}", response_model=ClinicalNoteResponse)
async def update_clinical_note(
    note_id: str,
    note_in: ClinicalNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    """Immutable Note Versioning (D5).
    Editing a clinical note NEVER overwrites the old record.
    It marks the preceding note as is_latest=False and creates a new version entry
    (version = parent_version + 1) with full lineage tracing (root_note_id & parent_note_id).
    """
    query = await db.execute(select(ClinicalNote).where(ClinicalNote.id == note_id, ClinicalNote.doctor_id == current_doctor.id))
    old_note = query.scalars().first()
    if not old_note:
        raise HTTPException(status_code=404, detail="Clinical note not found or access denied")

    old_note.is_latest = False

    root_id = old_note.root_note_id or old_note.id
    fmt_type = (note_in.format_type or old_note.format_type).upper()

    soap_subj = note_in.soap_subjective if note_in.soap_subjective is not None else old_note.soap_subjective
    soap_obj = note_in.soap_objective if note_in.soap_objective is not None else old_note.soap_objective
    soap_assess = note_in.soap_assessment if note_in.soap_assessment is not None else old_note.soap_assessment
    soap_pln = note_in.soap_plan if note_in.soap_plan is not None else old_note.soap_plan

    if fmt_type == "SOAP":
        note_text = note_in.note_text or (
            f"Subjective: {soap_subj or 'N/A'}\n"
            f"Objective: {soap_obj or 'N/A'}\n"
            f"Assessment: {soap_assess or 'N/A'}\n"
            f"Plan: {soap_pln or 'N/A'}"
        )
    else:
        note_text = note_in.note_text or old_note.note_text

    new_note = ClinicalNote(
        patient_id=old_note.patient_id,
        doctor_id=current_doctor.id,
        note_text=note_text,
        version=old_note.version + 1,
        root_note_id=root_id,
        parent_note_id=old_note.id,
        is_latest=True,
        format_type=fmt_type,
        soap_subjective=soap_subj,
        soap_objective=soap_obj,
        soap_assessment=soap_assess,
        soap_plan=soap_pln
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

@router.get("/notes/{note_id}/history", response_model=List[ClinicalNoteResponse])
async def get_clinical_note_history(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    """View full audit trail & version history of a clinical note (D5)."""
    query = await db.execute(select(ClinicalNote).where(ClinicalNote.id == note_id, ClinicalNote.doctor_id == current_doctor.id))
    note = query.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")

    root_id = note.root_note_id or note.id
    history_query = await db.execute(
        select(ClinicalNote)
        .where(
            (ClinicalNote.id == root_id) | (ClinicalNote.root_note_id == root_id)
        )
        .order_by(ClinicalNote.version.asc())
    )
    return history_query.scalars().all()

@router.get("/notes/search", response_model=List[ClinicalNoteResponse])
async def search_clinical_notes(
    q: str = Query(..., min_length=1, description="Search term for clinical notes"),
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    """Semantic & keyword search across a doctor's own clinical notes (D5)."""
    pattern = f"%{q.strip()}%"
    query = await db.execute(
        select(ClinicalNote)
        .where(
            ClinicalNote.doctor_id == current_doctor.id,
            ClinicalNote.is_latest == True,
            (
                ClinicalNote.note_text.ilike(pattern) |
                ClinicalNote.soap_subjective.ilike(pattern) |
                ClinicalNote.soap_objective.ilike(pattern) |
                ClinicalNote.soap_assessment.ilike(pattern) |
                ClinicalNote.soap_plan.ilike(pattern)
            )
        )
        .order_by(ClinicalNote.updated_at.desc())
    )
    return query.scalars().all()

@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_doctor_appointments(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    query = await db.execute(
        select(Appointment)
        .where(
            (Appointment.doctor_id == current_doctor.id)
            | (Appointment.doctor_id.is_(None))
        )
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
    current_doctor: User = Depends(get_current_verified_doctor)
):
    query = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = query.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    valid_statuses = ["requested", "confirmed", "completed", "cancelled", "no_show", "waitlisted"]
    if status_in.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from {valid_statuses}")

    if appt.doctor_id and appt.doctor_id != current_doctor.id:
        raise HTTPException(status_code=403, detail="This appointment belongs to another doctor")

    appt.status = status_in.status
    appt.doctor_id = current_doctor.id
    appt.updated_at = datetime.utcnow()
    
    if appt.status == "confirmed" and not appt.video_room_url and appt.consultation_type == "video_call":
        appt.video_room_url = f"https://meet.jit.si/vr-health-{appt.id}"

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

@router.post("/appointments/{appointment_id}/triage-action", response_model=AppointmentResponse)
async def process_appointment_triage_decision(
    appointment_id: str,
    triage_in: AppointmentTriageRequest,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    """Doctor Triage Decision Engine (D4).
    Enables clinicians to review patient problem descriptions and decide the consultation mode:
      1. 'accept_in_person' -> Confirmed in-person clinic appointment (sets location_notes).
      2. 'accept_video' -> Confirmed WebRTC video call (generates Jitsi room link).
      3. 'open_chat' -> Confirmed chat consultation (creates ChatSession & sends initial message).
      4. 'waitlist' -> Sets status to waitlisted.
      5. 'no_show' -> Marks patient as no-show.
      6. 'cancel' -> Cancels appointment.
    """
    query = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = query.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    action = triage_in.action.lower()
    appt.doctor_id = current_doctor.id
    appt.updated_at = datetime.utcnow()

    if action == "accept_in_person":
        appt.status = "confirmed"
        appt.consultation_type = "in_person"
        appt.location_notes = triage_in.location_notes or "Main Clinic, Room 101"

    elif action == "accept_video":
        appt.status = "confirmed"
        appt.consultation_type = "video_call"
        appt.video_room_url = f"https://meet.jit.si/vr-health-{appt.id}"
        appt.location_notes = triage_in.location_notes or "Online WebRTC Video Room"

    elif action == "open_chat":
        appt.status = "confirmed"
        appt.consultation_type = "chat"
        
        if not appt.chat_session_id:
            chat_title = f"Consultation: {appt.reason[:30] if appt.reason else 'Direct Doctor Chat'}"
            chat_session = ChatSession(user_id=appt.patient_id, title=chat_title)
            db.add(chat_session)
            await db.commit()
            await db.refresh(chat_session)
            
            init_msg = triage_in.initial_message or f"Hello, I reviewed your request regarding '{appt.reason or 'your concern'}'. Let's discuss here."
            chat_msg = ChatMessage(
                session_id=chat_session.id,
                sender="doctor",
                content=init_msg
            )
            db.add(chat_msg)
            appt.chat_session_id = chat_session.id
            appt.location_notes = "Direct Consultation Chat Active"

    elif action == "waitlist":
        appt.status = "waitlisted"

    elif action == "no_show":
        appt.status = "no_show"

    elif action == "cancel":
        appt.status = "cancelled"

    else:
        raise HTTPException(status_code=400, detail="Invalid triage action. Choose from accept_in_person, accept_video, open_chat, waitlist, no_show, cancel")

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

@router.get("/appointments/{appointment_id}/ical")
async def download_doctor_appointment_ical(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    """Download standard iCalendar (.ics) event file for Doctor (D4)."""
    query = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = query.scalars().first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    p_query = await db.execute(select(User).where(User.id == appt.patient_id))
    patient = p_query.scalars().first()
    patient_identifier = patient.email if patient else str(appt.patient_id)

    location_url = appt.video_room_url or appt.location_notes or "Online Consultation"
    summary = f"Doctor Consultation with {patient_identifier} ({appt.consultation_type or appt.preferred_mode})"
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
        f"UID:doctor-appt-{appt.id}@mindora.health\r\n"
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
        headers={"Content-Disposition": f"attachment; filename=doctor-appointment-{appt.id}.ics"}
    )

@router.get("/patient/{patient_id}/mood-summary")
async def get_patient_mood_summary(
    patient_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    """Longitudinal mood trend summary for doctors (D3b).
    Computes 30-day average mood score, volatility (stddev), top tags, and trajectory.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = await db.execute(
        select(MoodEntry)
        .where(
            MoodEntry.user_id == patient_id,
            MoodEntry.created_at >= cutoff
        )
        .order_by(MoodEntry.created_at.asc())
    )
    entries = query.scalars().all()
    
    if not entries:
        return {
            "patient_id": patient_id,
            "period_days": days,
            "entry_count": 0,
            "average_mood": None,
            "volatility": 0.0,
            "trajectory": "no_data",
            "top_tags": []
        }
        
    scores = [e.mood_score for e in entries]
    avg_mood = round(mean(scores), 2)
    volatility = round(pstdev(scores), 2) if len(scores) > 1 else 0.0
    
    if len(scores) >= 2:
        mid = len(scores) // 2
        first_half = mean(scores[:mid])
        second_half = mean(scores[mid:])
        if second_half - first_half >= 0.5:
            trajectory = "improving"
        elif first_half - second_half >= 0.5:
            trajectory = "declining"
        else:
            trajectory = "stable"
    else:
        trajectory = "stable"
        
    tag_counts = {}
    for e in entries:
        if e.tags and isinstance(e.tags, list):
            for t in e.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "patient_id": patient_id,
        "period_days": days,
        "entry_count": len(entries),
        "average_mood": avg_mood,
        "volatility": volatility,
        "trajectory": trajectory,
        "top_tags": [{"tag": t[0], "count": t[1]} for t in top_tags]
    }
