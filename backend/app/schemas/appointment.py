from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class AppointmentCreate(BaseModel):
    scheduled_at: datetime
    reason: Optional[str] = None
    doctor_id: Optional[UUID] = None
    preferred_mode: Optional[str] = "any"  # "video_call", "in_person", "chat", "any"

class AppointmentStatusUpdate(BaseModel):
    status: str  # "confirmed", "completed", "cancelled", "no_show", "waitlisted"

class AppointmentTriageRequest(BaseModel):
    action: str  # "accept_in_person", "accept_video", "open_chat", "cancel", "waitlist", "no_show"
    location_notes: Optional[str] = None  # e.g., "Main Clinic, Room 204"
    initial_message: Optional[str] = None  # Optional greeting to start direct consultation chat

class AppointmentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: Optional[UUID] = None
    scheduled_at: datetime
    status: str
    reason: Optional[str] = None
    preferred_mode: Optional[str] = "any"
    consultation_type: Optional[str] = None
    location_notes: Optional[str] = None
    video_room_url: Optional[str] = None
    chat_session_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    patient_email: Optional[str] = None
    patient_pseudonym: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    doctor_city: Optional[str] = None
    doctor_state: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
