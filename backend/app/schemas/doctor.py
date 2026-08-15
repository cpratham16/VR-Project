from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.schemas.screening import ScreeningResponse
from app.schemas.mood import MoodEntryResponse
from app.schemas.note import ClinicalNoteResponse

class TriagePatient(BaseModel):
    user_id: UUID
    email: str
    pseudonym: Optional[str] = None
    latest_phq9_score: Optional[int] = None
    latest_phq9_severity: Optional[str] = None
    latest_gad7_score: Optional[int] = None
    latest_gad7_severity: Optional[str] = None
    latest_mood_score: Optional[int] = None
    last_activity: Optional[datetime] = None
    risk_level: str  # "High", "Moderate", "Low", "Unassessed"
    risk_numeric: int  # 3=High, 2=Moderate, 1=Low, 0=Unassessed for sorting

class PatientDetailResponse(BaseModel):
    user_id: UUID
    email: str
    pseudonym: Optional[str] = None
    risk_level: str
    screenings: List[ScreeningResponse]
    mood_entries: List[MoodEntryResponse]
    clinical_notes: List[ClinicalNoteResponse]

class DoctorVerifyResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_verified: bool
