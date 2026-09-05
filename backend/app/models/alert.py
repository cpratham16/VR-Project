import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
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
    assigned_doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    sla_minutes = Column(Integer, default=15, nullable=False)
    sla_due_at = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False, nullable=False)
    escalation_tier = Column(Integer, default=1, nullable=False)  # Tier 1 (Assigned), Tier 2 (On-call pool), Tier 3 (Crisis hotline 988/Security)
    escalation_history = Column(Text, nullable=True)  # JSON text log of tier updates
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
