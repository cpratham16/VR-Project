import pytest
import uuid
from app.models.user import User
from app.models.note import ClinicalNote
from app.core.database import AsyncSessionLocal, engine
from app.schemas.note import ClinicalNoteCreate, ClinicalNoteUpdate
from app.api.v1.doctor import (
    create_clinical_note,
    update_clinical_note,
    get_clinical_note_history,
    search_clinical_notes
)
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_soap_note_creation_and_versioned_editing():
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        patient = User(id=patient_id, email=f"pat_note_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient")
        doctor = User(id=doctor_id, email=f"doc_note_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="doctor")
        db.add_all([patient, doctor])
        await db.commit()

        # 1. Create initial SOAP note (v1)
        soap_in = ClinicalNoteCreate(
            format_type="SOAP",
            soap_subjective="Patient reports acute exam anxiety and insomnia.",
            soap_objective="PHQ-9 score 12, GAD-7 score 14. Heart rate 88 bpm.",
            soap_assessment="Moderate anxiety secondary to academic stress.",
            soap_plan="Assigned WebVR glossophobia module & recommended 4-7-8 breathing."
        )
        v1_note = await create_clinical_note(patient_id=str(patient_id), note_in=soap_in, db=db, current_doctor=doctor)
        assert v1_note.version == 1
        assert v1_note.is_latest is True
        assert v1_note.format_type == "SOAP"
        assert "Subjective:" in v1_note.note_text

        # 2. Perform Versioned Edit (v2) - Immutability test
        edit_in = ClinicalNoteUpdate(
            soap_assessment="Updated Assessment: Moderate anxiety with panic component.",
            soap_plan="Assigned WebVR glossophobia module + 2 additional exposure steps."
        )
        v2_note = await update_clinical_note(note_id=str(v1_note.id), note_in=edit_in, db=db, current_doctor=doctor)
        
        assert v2_note.version == 2
        assert v2_note.is_latest is True
        assert v2_note.root_note_id == v1_note.id
        assert v2_note.parent_note_id == v1_note.id
        assert "panic component" in v2_note.soap_assessment

        # Verify v1 note still exists in DB as non-latest audit record
        v1_db = (await db.execute(select(ClinicalNote).where(ClinicalNote.id == v1_note.id))).scalars().first()
        assert v1_db.is_latest is False
        assert v1_db.version == 1

        # 3. View Full Version History Audit Chain
        history = await get_clinical_note_history(note_id=str(v2_note.id), db=db, current_doctor=doctor)
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2

        # 4. Search Notes
        search_res = await search_clinical_notes(q="panic component", db=db, current_doctor=doctor)
        assert len(search_res) == 1
        assert search_res[0].id == v2_note.id

        # Cleanup (delete child version first to satisfy FK constraint)
        await db.delete(v2_note)
        await db.commit()
        await db.delete(v1_db)
        await db.delete(patient)
        await db.delete(doctor)
        await db.commit()
