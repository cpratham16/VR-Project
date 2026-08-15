from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ClinicalNoteCreate(BaseModel):
    note_text: str

class ClinicalNoteResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    note_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
