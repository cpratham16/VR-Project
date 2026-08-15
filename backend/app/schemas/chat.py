from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ChatMessageCreate(BaseModel):
    message: str
    session_id: Optional[UUID] = None

class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    sender: str
    content: str
    risk_flag: bool
    rag_context_used: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    messages: List[ChatMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)
