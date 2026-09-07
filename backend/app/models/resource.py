from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=False, default="pdf")  # pdf, book, article, video
    category = Column(String(50), nullable=False, default="general")  # anxiety, mindfulness, sleep, academic, general
    file_url = Column(String(512), nullable=True)
    thumbnail_url = Column(String(512), nullable=True)
    author = Column(String(255), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class UserResourceProgress(Base):
    __tablename__ = "user_resource_progress"
    __table_args__ = (UniqueConstraint("user_id", "resource_id", name="uq_user_resource_progress"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    saved_for_later = Column(Boolean, default=False, nullable=False)
    progress_percent = Column(Integer, default=0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

