from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Newsletter(Base):
    __tablename__ = "newsletters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(String(512), nullable=True)
    author = Column(String(255), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
