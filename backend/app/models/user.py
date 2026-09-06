import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="patient", nullable=False)  # "patient", "doctor", "admin"
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Important for doctors later
    state = Column(String, nullable=True)
    city = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    diary_pin_hash = Column(String, nullable=True)  # For diary privacy lock
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chat_room_participants = relationship("ChatRoomParticipant", back_populates="user")
    chat_room_messages = relationship("ChatRoomMessage", back_populates="sender")
