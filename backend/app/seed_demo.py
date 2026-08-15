"""Seed full-stack demo data for a cold-demo run-through.

Idempotent: users are skipped if their email already exists. Run AFTER
`alembic upgrade head` and the VR scenario seed:

    python -m app.seed_vr
    python -m app.seed_demo

Demo credentials printed at the end of execution.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.patient import PatientProfile, ConsentRecord
from app.models.screening import ScreeningResult
from app.models.mood import MoodEntry
from app.models.note import ClinicalNote
from app.models.appointment import Appointment
from app.models.chat import ChatSession, ChatMessage
from app.models.alert import RiskAlert
from app.models.community import CommunityPost
from app.models.vr import VRScenario, VRSession, VRTelemetry
from app.schemas.screening import calculate_phq9_severity, calculate_gad7_severity
from app.services.anonymizer import run_aggregation

DEMO = {
    "admin": {"email": "admin@campus.edu", "password": "admin123", "role": "admin",
              "state": "Maharashtra", "city": "Pune"},
    "doctors": [
        {"email": "doctor1@campus.edu", "password": "doc123", "role": "doctor",
         "state": "Delhi", "city": "New Delhi"},
        {"email": "doctor2@campus.edu", "password": "doc123", "role": "doctor",
         "state": "Karnataka", "city": "Bengaluru"},
    ],
    "patients": [
        {"email": "alice@campus.edu", "password": "pass123", "role": "patient",
         "state": "Maharashtra", "city": "Pune", "pseudonym": "River_Fern"},
        {"email": "bob@campus.edu", "password": "pass123", "role": "patient",
         "state": "Delhi", "city": "New Delhi", "pseudonym": "Quiet_Oak"},
        {"email": "carol@campus.edu", "password": "pass123", "role": "patient",
         "state": "Karnataka", "city": "Bengaluru", "pseudonym": "Blue_Moon"},
        {"email": "dave@campus.edu", "password": "pass123", "role": "patient",
         "state": "Tamil Nadu", "city": "Chennai", "pseudonym": "Silent_Stream"},
        {"email": "eve@campus.edu", "password": "pass123", "role": "patient",
         "state": "Kerala", "city": "Kochi", "pseudonym": "Night_Harbor"},
    ],
}

# index -> severity profile per patient (PHQ-9 total, GAD-7 total)
SEVERITY_PROFILES = [
    {"phq9": 17, "gad7": 14},   # alice: moderate-severe / moderate
    {"phq9": 22, "gad7": 18},   # bob: severe / severe
    {"phq9": 7, "gad7": 6},     # carol: mild / mild
    {"phq9": 12, "gad7": 11},   # dave: moderate / moderate
    {"phq9": 3, "gad7": 3},     # eve: minimal / minimal
]

CATEGORIES = ["Academic Stress", "Exam Anxiety", "Peer Support", "General Wellness"]

POSTS = [
    ("Final exams have been overwhelming. Any tips for staying grounded?", "Exam Anxiety"),
    ("Feeling proud of making it to my third therapy session today!", "Peer Support"),
    ("How do you all handle stage fear before presentations?", "General Wellness"),
    ("Worried I won't meet my parents' expectations this semester.", "Academic Stress"),
]

FLAGGED_POST = ("I feel like giving up on everything. Nothing matters anymore.", "Academic Stress")


async def seed():
    async with AsyncSessionLocal() as db:
        # Ensure VR scenarios exist
        scenarios = (await db.execute(select(VRScenario))).scalars().all()
        if not scenarios:
            print("No VR scenarios found — run `python -m app.seed_vr` first.")
            return

        admin = await get_or_create_user(db, DEMO["admin"])
        doctors = [await get_or_create_user(db, d) for d in DEMO["doctors"]]
        patients = [await get_or_create_user(db, p) for p in DEMO["patients"]]
        await db.commit()

        for i, p in enumerate(patients):
            data = DEMO["patients"][i]
            await ensure_patient_profile(db, p, data["pseudonym"])
            await ensure_consent(db, p)
            await seed_screenings(db, p, SEVERITY_PROFILES[i])
            await seed_mood_entries(db, p, i)
            await seed_appointment(db, p, doctors[i % len(doctors)])
            await seed_risk_alerts(db, p, SEVERITY_PROFILES[i], doctors[i % len(doctors)])
            await seed_chat(db, p)
            await seed_vr_sessions(db, p, doctors[i % len(doctors)], scenarios, i)
            await seed_notes(db, p, doctors[i % len(doctors)])

        await seed_community(db, patients, doctors)
        await db.commit()

        # Populate the anonymized admin reporting store
        summary = await run_aggregation(db)

        print("\n=== DEMO CREDENTIALS ===")
        print("Admin  : admin@campus.edu / admin123")
        print("Doctor : doctor1@campus.edu / doc123")
        print("Doctor : doctor2@campus.edu / doc123")
        for p in DEMO["patients"]:
            print(f"Patient: {p['email']} / pass123")
        print(f"\nAnonymization pipeline ran: {summary['rows_written']} region-periods written.")
        print("Seeding complete.")


async def get_or_create_user(db, data) -> User:
    existing = (await db.execute(select(User).where(User.email == data["email"]))).scalars().first()
    if existing:
        return existing
    user = User(
        email=data["email"],
        hashed_password=get_password_hash(data["password"]),
        role=data["role"],
        state=data.get("state"),
        city=data.get("city"),
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    return user


async def ensure_patient_profile(db, user: User, pseudonym: str):
    existing = (await db.execute(select(PatientProfile).where(PatientProfile.user_id == user.id))).scalars().first()
    if not existing:
        db.add(PatientProfile(user_id=user.id, pseudonym=pseudonym))


async def ensure_consent(db, user: User):
    existing = (await db.execute(select(ConsentRecord).where(ConsentRecord.user_id == user.id))).scalars().first()
    if not existing:
        db.add(ConsentRecord(
            user_id=user.id,
            consent_version="v1",
            agreed_to_ai_processing=True,
            agreed_to_data_usage=True,
        ))


async def seed_screenings(db, user: User, profile: dict):
    now = datetime.utcnow()
    # PHQ-9 answers: distribute total across 9 items
    phq9_answers = distribute_answers(profile["phq9"], 9)
    phq9_total = sum(phq9_answers)
    db.add(ScreeningResult(
        user_id=user.id,
        screening_type="PHQ-9",
        answers=phq9_answers,
        total_score=phq9_total,
        severity_band=calculate_phq9_severity(phq9_total),
        created_at=now - timedelta(days=12),
    ))
    gad7_answers = distribute_answers(profile["gad7"], 7)
    gad7_total = sum(gad7_answers)
    db.add(ScreeningResult(
        user_id=user.id,
        screening_type="GAD-7",
        answers=gad7_answers,
        total_score=gad7_total,
        severity_band=calculate_gad7_severity(gad7_total),
        created_at=now - timedelta(days=12),
    ))


def distribute_answers(total: int, n: int) -> list:
    base = total // n
    rem = total % n
    answers = [base] * n
    for i in range(rem):
        answers[i] += 1
    return answers


async def seed_mood_entries(db, user: User, seed_offset: int):
    existing = (await db.execute(select(MoodEntry).where(MoodEntry.user_id == user.id))).scalars().first()
    if existing:
        return
    now = datetime.utcnow()
    for day in range(14):
        # sinusoidal variation so each patient has a distinct pattern
        score = max(1, min(5, round(3 + ((seed_offset + day) % 5) * 0.4 - (day % 3) * 0.3)))
        db.add(MoodEntry(
            user_id=user.id,
            mood_score=score,
            tags=["general"],
            journal_text=None,
            created_at=now - timedelta(days=13 - day),
        ))


async def seed_appointment(db, user: User, doctor: User):
    existing = (await db.execute(select(Appointment).where(Appointment.patient_id == user.id))).scalars().first()
    if not existing:
        db.add(Appointment(
            patient_id=user.id,
            doctor_id=doctor.id,
            scheduled_at=datetime.utcnow() + timedelta(days=3),
            status="confirmed",
            reason="Follow-up review of screening results and mood tracking.",
        ))


async def seed_risk_alerts(db, user: User, profile: dict, doctor: User):
    existing = (await db.execute(select(RiskAlert).where(RiskAlert.user_id == user.id))).scalars().first()
    if existing:
        return
    now = datetime.utcnow()
    if profile["phq9"] >= 15:
        db.add(RiskAlert(
            user_id=user.id,
            severity="CRITICAL" if profile["phq9"] >= 20 else "HIGH",
            trigger_source="screening_high",
            details=f"PHQ-9 score {profile['phq9']} places this patient in the {calculate_phq9_severity(profile['phq9'])} range.",
            status="pending",
            created_at=now - timedelta(days=12),
        ))
        db.add(RiskAlert(
            user_id=user.id,
            severity="HIGH",
            trigger_source="chat_distress",
            details="Distress keyword scan flagged elevated language during an AI chat session.",
            status="pending",
            acknowledged_by_doctor_id=doctor.id,
            created_at=now - timedelta(days=6),
        ))
    else:
        db.add(RiskAlert(
            user_id=user.id,
            severity="MEDIUM",
            trigger_source="screening_high",
            details=f"PHQ-9 score {profile['phq9']} ({calculate_phq9_severity(profile['phq9'])} band) — routine follow-up advised.",
            status="resolved",
            acknowledged_by_doctor_id=doctor.id,
            created_at=now - timedelta(days=10),
            resolved_at=now - timedelta(days=9),
        ))


async def seed_chat(db, user: User):
    existing = (await db.execute(select(ChatSession).where(ChatSession.user_id == user.id))).scalars().first()
    if existing:
        return
    session = ChatSession(user_id=user.id, title="Evening check-in")
    db.add(session)
    await db.flush()
    msgs = [
        ("user", "I've been feeling anxious about my exams next week.", False, False),
        ("assistant", "That is completely understandable — exams can bring up a lot of pressure. Would you like to try a short breathing exercise together?", False, True),
        ("user", "Yes, that would help. Thank you.", False, False),
        ("assistant", "Let's begin: breathe in for four counts, hold for four, and exhale for six. Repeat that cycle five times and notice how your body responds.", False, True),
    ]
    for sender, content, risk, rag in msgs:
        db.add(ChatMessage(session_id=session.id, sender=sender, content=content, risk_flag=risk, rag_context_used=rag))


async def seed_vr_sessions(db, user: User, doctor: User, scenarios, idx: int):
    existing = (await db.execute(select(VRSession).where(VRSession.patient_id == user.id))).scalars().first()
    if existing:
        return
    now = datetime.utcnow()
    scenario = scenarios[idx % len(scenarios)]
    if idx % 2 == 0:
        completed = VRSession(
            patient_id=user.id,
            doctor_id=doctor.id,
            scenario_id=scenario.id,
            intensity_level="medium",
            duration_minutes=10,
            exposure_steps=5,
            instructions="Start with three slow breaths. Focus on grounding before advancing to the next stage.",
            status="completed",
            suds_pre=7,
            suds_post=4,
            patient_feedback="Noticed my heart racing early on but the breathing prompts really helped.",
            assigned_at=now - timedelta(days=8),
            started_at=now - timedelta(days=7),
            completed_at=now - timedelta(days=7),
        )
        db.add(completed)
        await db.flush()
        for step in range(1, 6):
            db.add(VRTelemetry(
                session_id=completed.id,
                timestamp=now - timedelta(days=7) + timedelta(minutes=step * 2),
                heart_rate=78 + step * 6,
                hrv_rmssd=52 - step * 4,
                stress_index=30 + step * 12,
                scene_stage=step,
            ))
        assigned = VRSession(
            patient_id=user.id,
            doctor_id=doctor.id,
            scenario_id=scenarios[(idx + 1) % len(scenarios)].id,
            intensity_level="high",
            duration_minutes=15,
            exposure_steps=6,
            instructions="Progress only when your distress feels manageable. The panic button is always available.",
            status="assigned",
            assigned_at=now - timedelta(days=1),
        )
        db.add(assigned)
    else:
        db.add(VRSession(
            patient_id=user.id,
            doctor_id=doctor.id,
            scenario_id=scenario.id,
            intensity_level="low",
            duration_minutes=8,
            exposure_steps=4,
            instructions="A gentle first exposure. Focus on your breathing and use the railing to steady yourself.",
            status="assigned",
            assigned_at=now - timedelta(days=2),
        ))


async def seed_notes(db, user: User, doctor: User):
    existing = (await db.execute(select(ClinicalNote).where(ClinicalNote.patient_id == user.id))).scalars().first()
    if not existing:
        db.add(ClinicalNote(
            patient_id=user.id,
            doctor_id=doctor.id,
            note_text="Patient is engaged with mood tracking and responding well to psychoeducation. Will review VR exposure progress at next session.",
        ))


async def seed_community(db, patients, doctors):
    existing = (await db.execute(select(CommunityPost))).scalars().first()
    if existing:
        return
    now = datetime.utcnow()
    for i, (content, category) in enumerate(POSTS):
        patient = patients[i % len(patients)]
        db.add(CommunityPost(
            user_id=patient.id,
            author_pseudonym=DEMO["patients"][i % len(DEMO["patients"])]["pseudonym"],
            category=category,
            title=content.split(".")[0],
            content=content,
            is_flagged=False,
            moderation_status="approved",
            created_at=now - timedelta(days=i),
        ))
    flagged = patients[1]
    db.add(CommunityPost(
        user_id=flagged.id,
        author_pseudonym=DEMO["patients"][1]["pseudonym"],
        category=FLAGGED_POST[1],
        title="I feel like giving up",
        content=FLAGGED_POST[0],
        is_flagged=True,
        moderation_status="flagged_pending",
        created_at=now - timedelta(hours=3),
    ))


if __name__ == "__main__":
    asyncio.run(seed())
