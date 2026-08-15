from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class PanicRequest(BaseModel):
    location_note: Optional[str] = "Campus Main Premises"

class RiskAlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    patient_pseudonym: Optional[str] = "Anonymous Student"
    severity: str
    trigger_source: str
    details: str
    status: str
    acknowledged_by_doctor_id: Optional[UUID] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AcknowledgeAlertRequest(BaseModel):
    resolution_notes: Optional[str] = None
