from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class DiaryEntryCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    entry_date: Optional[datetime] = None

class DiaryEntryUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    entry_date: Optional[datetime] = None

class DiaryEntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str]
    content: str
    entry_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True