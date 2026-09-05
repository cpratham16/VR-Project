import pytest
import uuid
from datetime import datetime, timedelta
from app.models.user import User
from app.models.appointment import Appointment
from app.models.chat import ChatSession, ChatMessage
from app.core.database import AsyncSessionLocal, engine
from app.schemas.appointment import AppointmentCreate, AppointmentTriageRequest, AppointmentStatusUpdate
from app.api.v1.patient import request_appointment, download_appointment_ical
from app.api.v1.doctor import process_appointment_triage_decision, update_appointment_status, download_doctor_appointment_ical
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_appointment_request_with_preferred_mode():
    patient_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        patient = User(id=patient_id, email=f"patient_sched_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient")
        db.add(patient)
        await db.commit()

        appt_in = AppointmentCreate(
            scheduled_at=datetime.utcnow() + timedelta(days=2),
            reason="Exams anxiety and trouble sleeping",
            preferred_mode="video_call"
        )
        res = await request_appointment(appt_in=appt_in, db=db, current_user=patient)
        assert res["preferred_mode"] == "video_call"
        assert res["status"] == "requested"

        # Cleanup
        db_appt = (await db.execute(select(Appointment).where(Appointment.id == res["id"]))).scalars().first()
        await db.delete(db_appt)
        await db.delete(patient)
        await db.commit()

@pytest.mark.asyncio
async def test_doctor_triage_decision_engine():
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        patient = User(id=patient_id, email=f"patient_triage_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient")
        doctor = User(id=doctor_id, email=f"doctor_triage_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="doctor")
        db.add_all([patient, doctor])
        await db.commit()

        # 1. Accept Video Call
        appt1 = Appointment(patient_id=patient_id, scheduled_at=datetime.utcnow() + timedelta(days=1), reason="Panic attacks", status="requested")
        db.add(appt1)
        await db.commit()

        triage_video = AppointmentTriageRequest(action="accept_video")
        res_video = await process_appointment_triage_decision(appointment_id=str(appt1.id), triage_in=triage_video, db=db, current_doctor=doctor)
        assert res_video.status == "confirmed"
        assert res_video.consultation_type == "video_call"
        assert f"https://meet.jit.si/vr-health-{appt1.id}" == res_video.video_room_url

        # 2. Accept In-Person
        appt2 = Appointment(patient_id=patient_id, scheduled_at=datetime.utcnow() + timedelta(days=2), reason="Severe depression", status="requested")
        db.add(appt2)
        await db.commit()

        triage_person = AppointmentTriageRequest(action="accept_in_person", location_notes="Building B, Room 204")
        res_person = await process_appointment_triage_decision(appointment_id=str(appt2.id), triage_in=triage_person, db=db, current_doctor=doctor)
        assert res_person.status == "confirmed"
        assert res_person.consultation_type == "in_person"
        assert res_person.location_notes == "Building B, Room 204"

        # 3. Open Direct Consultation Chat
        appt3 = Appointment(patient_id=patient_id, scheduled_at=datetime.utcnow() + timedelta(days=3), reason="General inquiry", status="requested")
        db.add(appt3)
        await db.commit()

        triage_chat = AppointmentTriageRequest(action="open_chat", initial_message="Hi! Let's talk about your inquiry.")
        res_chat = await process_appointment_triage_decision(appointment_id=str(appt3.id), triage_in=triage_chat, db=db, current_doctor=doctor)
        assert res_chat.status == "confirmed"
        assert res_chat.consultation_type == "chat"
        assert res_chat.chat_session_id is not None

        # Verify chat session & message were actually created in DB
        chat_sess = (await db.execute(select(ChatSession).where(ChatSession.id == res_chat.chat_session_id))).scalars().first()
        assert chat_sess is not None
        chat_msg = (await db.execute(select(ChatMessage).where(ChatMessage.session_id == chat_sess.id))).scalars().first()
        assert chat_msg.content == "Hi! Let's talk about your inquiry."
        assert chat_msg.sender == "doctor"

        # 4. Status update to no_show & waitlist
        res_noshow = await update_appointment_status(appointment_id=str(appt1.id), status_in=AppointmentStatusUpdate(status="no_show"), db=db, current_doctor=doctor)
        assert res_noshow.status == "no_show"

        res_waitlist = await update_appointment_status(appointment_id=str(appt2.id), status_in=AppointmentStatusUpdate(status="waitlisted"), db=db, current_doctor=doctor)
        assert res_waitlist.status == "waitlisted"

        # 5. Download iCal (.ics)
        ical_resp = await download_appointment_ical(appointment_id=str(appt1.id), db=db, current_user=patient)
        assert ical_resp.media_type == "text/calendar"
        assert b"BEGIN:VCALENDAR" in ical_resp.body
        assert b"https://meet.jit.si/vr-health-" in ical_resp.body

        # Cleanup
        await db.delete(chat_msg)
        await db.delete(chat_sess)
        await db.delete(appt1)
        await db.delete(appt2)
        await db.delete(appt3)
        await db.delete(patient)
        await db.delete(doctor)
        await db.commit()
