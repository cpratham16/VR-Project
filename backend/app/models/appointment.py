import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String, default="requested", nullable=False)  # "requested", "confirmed", "completed", "cancelled", "no_show", "waitlisted"
    reason = Column(Text, nullable=True)
    preferred_mode = Column(String, default="any", nullable=True)  # "video_call", "in_person", "chat", "any"
    consultation_type = Column(String, nullable=True)  # "in_person", "video_call", "chat"
    location_notes = Column(Text, nullable=True)
    video_room_url = Column(String, nullable=True)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
