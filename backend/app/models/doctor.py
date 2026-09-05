import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    license_number = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    languages = Column(Text, nullable=False, default="[]")
    credential_filename = Column(String, nullable=True)
    credential_path = Column(String, nullable=True)
    uploaded_at = Column(DateTime, nullable=True)
    review_status = Column(String, nullable=False, default="pending")  # "pending" | "approved" | "rejected"
    rejection_reason = Column(Text, nullable=True)
    reviewed_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def languages_list(self) -> list:
        try:
            return json.loads(self.languages)
        except Exception:
            return []
