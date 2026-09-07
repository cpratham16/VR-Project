import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class NotificationRecord(Base):
    __tablename__ = "notification_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("risk_alerts.id"), nullable=True)
    recipient_type = Column(String, nullable=False)  # "secondary_contact" | "on_call_doctor" | "backup_pool" | "student_announcement"
    recipient_label = Column(String, nullable=True)  # e.g. phone number or doctor email
    channel = Column(String, nullable=False, default="sms")  # "sms" | "email" | "in_app"
    status = Column(String, nullable=False, default="simulated")  # "simulated" | "sent" | "failed"
    content_preview = Column(Text, nullable=True)
    link_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
