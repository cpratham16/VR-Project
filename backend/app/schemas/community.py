from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class CommunityCommentCreate(BaseModel):
    content: str

class CommunityCommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    author_pseudonym: str
    content: str
    is_flagged: bool
    moderation_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommunityPostCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "General Wellness"

class CommunityPostResponse(BaseModel):
    id: UUID
    author_pseudonym: str
    category: str
    title: str
    content: str
    is_flagged: bool
    moderation_status: str
    created_at: datetime
    updated_at: datetime
    comment_count: int = 0
    comments: List[CommunityCommentResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ModerationActionRequest(BaseModel):
    action: str  # "approve", "reject"
    notes: Optional[str] = None
