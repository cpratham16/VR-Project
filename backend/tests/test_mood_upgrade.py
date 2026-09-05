import pytest
import uuid
from datetime import datetime, timedelta
from app.core.security import encrypt_text, decrypt_text
from app.models.mood import MoodEntry
from app.models.user import User
from app.core.database import AsyncSessionLocal, engine
from sqlalchemy.future import select

def test_fernet_encryption_roundtrip():
    plaintext = "Deep personal reflection: I felt anxious today before the exam."
    ciphertext = encrypt_text(plaintext)
    assert ciphertext != plaintext
    assert ciphertext.startswith("gAAAA")
    
    decrypted = decrypt_text(ciphertext)
    assert decrypted == plaintext

def test_fernet_legacy_unencrypted_fallback():
    raw_legacy = "Old unencrypted journal entry."
    assert decrypt_text(raw_legacy) == raw_legacy

@pytest.mark.asyncio
async def test_mood_journal_db_encryption():
    user_id = uuid.uuid4()
    raw_secret = "Confidential thoughts: feeling down about academic pressure."
    encrypted_secret = encrypt_text(raw_secret)
    
    async with AsyncSessionLocal() as db:
        # Create user first
        user = User(id=user_id, email=f"mood_user_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient")
        db.add(user)
        await db.commit()
        
        # Add mood entry with encrypted journal text
        entry = MoodEntry(
            user_id=user_id,
            mood_score=2,
            tags=["exam_stress"],
            journal_text=encrypted_secret
        )
        db.add(entry)
        await db.commit()
        
        # 1. Assert raw DB record is ciphertext and does NOT contain plaintext
        res = await db.execute(select(MoodEntry).where(MoodEntry.id == entry.id))
        db_record = res.scalars().first()
        assert db_record.journal_text != raw_secret
        assert raw_secret not in db_record.journal_text
        assert db_record.journal_text.startswith("gAAAA")
        
        # 2. Assert decryption retrieves exact original text
        assert decrypt_text(db_record.journal_text) == raw_secret
        
        # Clean up
        await db.delete(db_record)
        await db.delete(user)
        await db.commit()

@pytest.mark.asyncio
async def test_doctor_mood_summary_and_export():
    patient_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as db:
        user = User(id=patient_id, email=f"patient_export_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient", state="Maharashtra", city="Pune")
        db.add(user)
        await db.commit()
        
        # Add 3 mood entries to test summary and export
        m1 = MoodEntry(user_id=patient_id, mood_score=2, tags=["stress"], journal_text=encrypt_text("Day 1 bad"))
        m2 = MoodEntry(user_id=patient_id, mood_score=3, tags=["stress", "work"], journal_text=encrypt_text("Day 2 okay"))
        m3 = MoodEntry(user_id=patient_id, mood_score=4, tags=["work"], journal_text=encrypt_text("Day 3 better"))
        db.add_all([m1, m2, m3])
        await db.commit()
        
        # Test doctor mood summary computation
        from app.api.v1.doctor import get_patient_mood_summary
        summary = await get_patient_mood_summary(patient_id=str(patient_id), days=30, db=db, current_doctor=user)
        assert summary["entry_count"] == 3
        assert summary["average_mood"] == 3.0
        assert summary["trajectory"] == "improving"
        assert len(summary["top_tags"]) == 2
        
        # Test patient export
        from app.api.v1.patient import export_patient_data
        export = await export_patient_data(db=db, current_user=user)
        assert export["user_profile"]["role"] == "patient"
        assert len(export["mood_history"]) == 3
        assert export["mood_history"][0]["journal_text"] in ["Day 1 bad", "Day 2 okay", "Day 3 better"]
        
        # Cleanup
        await db.delete(m1)
        await db.delete(m2)
        await db.delete(m3)
        await db.delete(user)
        await db.commit()
