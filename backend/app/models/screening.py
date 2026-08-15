import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

class ScreeningResult(Base):
    __tablename__ = "screening_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    screening_type = Column(String, nullable=False)  # "PHQ-9" or "GAD-7"
    answers = Column(JSON, nullable=False)  # list of integer scores [0..3]
    total_score = Column(Integer, nullable=False)
    severity_band = Column(String, nullable=False)  # e.g., Minimal, Mild, Moderate, Moderately Severe, Severe
    created_at = Column(DateTime, default=datetime.utcnow)
