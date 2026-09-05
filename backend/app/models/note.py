import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    root_note_id = Column(UUID(as_uuid=True), ForeignKey("clinical_notes.id"), nullable=True)
    parent_note_id = Column(UUID(as_uuid=True), ForeignKey("clinical_notes.id"), nullable=True)
    is_latest = Column(Boolean, default=True, nullable=False)
    format_type = Column(String, default="free_text", nullable=False)  # "free_text", "SOAP"
    soap_subjective = Column(Text, nullable=True)
    soap_objective = Column(Text, nullable=True)
    soap_assessment = Column(Text, nullable=True)
    soap_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
