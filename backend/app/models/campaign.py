from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    audience_type = Column(String(50), nullable=False, default="all")  # all, students, doctors
    delivery_channels = Column(String(100), nullable=False, default="email,in_app")  # comma-separated
    status = Column(String(50), nullable=False, default="draft")  # draft, scheduled, sent, failed
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class EmailRecipient(Base):
    __tablename__ = "email_recipients"
    __table_args__ = (UniqueConstraint("campaign_id", "user_id", name="uq_campaign_recipient"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    campaign_id = Column(String(36), ForeignKey("email_campaigns.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, sent, failed
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
