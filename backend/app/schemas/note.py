from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ClinicalNoteCreate(BaseModel):
    note_text: Optional[str] = None
    format_type: Optional[str] = "free_text"  # "free_text", "SOAP"
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None

class ClinicalNoteUpdate(BaseModel):
    note_text: Optional[str] = None
    format_type: Optional[str] = None
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None

class ClinicalNoteResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    note_text: str
    version: int = 1
    root_note_id: Optional[UUID] = None
    parent_note_id: Optional[UUID] = None
    is_latest: bool = True
    format_type: str = "free_text"
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
