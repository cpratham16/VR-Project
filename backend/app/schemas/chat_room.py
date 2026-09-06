from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from enum import Enum

class ChatRoomType(str, Enum):
    GENERAL = "general_support"
    ACADEMIC = "academic_stress"
    ANXIETY = "anxiety_stress"
    WELLNESS = "wellness_discussion"

class ChatRoomBase(BaseModel):
    name: str
    room_type: ChatRoomType
    description: Optional[str] = None

class ChatRoomCreate(ChatRoomBase):
    pass

class ChatRoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ChatRoomResponse(BaseModel):
    id: UUID
    name: str
    room_type: ChatRoomType
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    participant_count: int = 0
    unread_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class ChatRoomListResponse(BaseModel):
    rooms: List[ChatRoomResponse]

class ChatRoomParticipantResponse(BaseModel):
    user_id: UUID
    room_id: UUID
    role: str
    joined_at: datetime
    last_read_at: Optional[datetime]
    is_muted: bool

    model_config = ConfigDict(from_attributes=True)

class ChatRoomMessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    reply_to_id: Optional[UUID] = None

class ChatRoomMessageUpdate(BaseModel):
    content: Optional[str] = None

class ChatRoomMessageResponse(BaseModel):
    id: UUID
    room_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    reply_to_id: Optional[UUID]
    is_deleted: bool
    edited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    sender_pseudonym: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChatRoomMessagesResponse(BaseModel):
    messages: List[ChatRoomMessageResponse]
    next_cursor: Optional[str] = None