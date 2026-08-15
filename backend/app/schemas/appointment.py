from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AppointmentCreate(BaseModel):
    scheduled_at: datetime
    reason: Optional[str] = None
    doctor_id: Optional[UUID] = None

class AppointmentStatusUpdate(BaseModel):
    status: str  # "confirmed", "completed", "cancelled"

class AppointmentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: Optional[UUID] = None
    scheduled_at: datetime
    status: str
    reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    patient_email: Optional[str] = None
    patient_pseudonym: Optional[str] = None

    class Config:
        from_attributes = True
