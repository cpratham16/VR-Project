import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.core.database import Base

class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mood_score = Column(Integer, nullable=False)  # 1 to 5
    tags = Column(JSON, default=list, nullable=False)  # List[str]
    journal_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
