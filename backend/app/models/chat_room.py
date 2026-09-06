import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ChatRoomType(str, enum.Enum):
    GENERAL = "general_support"
    ACADEMIC = "academic_stress"
    ANXIETY = "anxiety_stress"
    WELLNESS = "wellness_discussion"

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    room_type = Column(Enum(ChatRoomType), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    participants = relationship("ChatRoomParticipant", back_populates="room")
    messages = relationship("ChatRoomMessage", back_populates="room")

class ChatRoomParticipant(Base):
    __tablename__ = "chat_room_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member", nullable=False)  # member, moderator, doctor
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_read_at = Column(DateTime, nullable=True)
    is_muted = Column(Boolean, default=False, nullable=False)
    
    room = relationship("ChatRoom", back_populates="participants")
    user = relationship("User", back_populates="chat_room_participants")

class ChatRoomMessage(Base):
    __tablename__ = "chat_room_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text", nullable=False)  # text, system, file
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("chat_room_messages.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User", back_populates="chat_room_messages")
    reply_to = relationship("ChatRoomMessage", remote_side="ChatRoomMessage.id")