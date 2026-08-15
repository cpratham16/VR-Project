import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    severity = Column(String, nullable=False)  # "CRITICAL", "HIGH", "MEDIUM"
    trigger_source = Column(String, nullable=False)  # "panic_sos", "chat_distress", "screening_high"
    details = Column(Text, nullable=False)
    status = Column(String, default="pending", nullable=False)  # "pending", "acknowledged", "resolved"
    acknowledged_by_doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
