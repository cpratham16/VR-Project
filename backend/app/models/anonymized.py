import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class RegionalAggregate(Base):
    """Anonymized regional reporting store.

    HARD BOUNDARY: This table contains NO columns capable of identifying an
    individual. No foreign keys, no user_id, no email, no pseudonym, no free
    text. Only region + period + numeric aggregates, as verified by the
    schema-review test (tests/test_anonymization.py).
    """

    __tablename__ = "regional_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    region = Column(String, nullable=False)          # e.g. "Pune, Maharashtra"
    period = Column(String, nullable=False)          # e.g. "2026-08" (YYYY-MM)

    total_patients = Column(Integer, default=0, nullable=False)
    screening_count = Column(Integer, default=0, nullable=False)
    phq9_minimal = Column(Integer, default=0, nullable=False)
    phq9_mild = Column(Integer, default=0, nullable=False)
    phq9_moderate = Column(Integer, default=0, nullable=False)
    phq9_moderately_severe = Column(Integer, default=0, nullable=False)
    phq9_severe = Column(Integer, default=0, nullable=False)
    gad7_minimal = Column(Integer, default=0, nullable=False)
    gad7_mild = Column(Integer, default=0, nullable=False)
    gad7_moderate = Column(Integer, default=0, nullable=False)
    gad7_severe = Column(Integer, default=0, nullable=False)
    avg_mood_score = Column(Float, default=0.0, nullable=False)
    mood_entry_count = Column(Integer, default=0, nullable=False)
    risk_alert_count = Column(Integer, default=0, nullable=False)
    vr_sessions_completed = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RegionalAggregate region={self.region} period={self.period}>"
