from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime
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
