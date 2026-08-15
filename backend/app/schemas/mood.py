from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class MoodEntryCreate(BaseModel):
    mood_score: int = Field(..., ge=1, le=5, description="Mood score from 1 (Severe Distress) to 5 (Excellent)")
    tags: List[str] = Field(default_factory=list)
    journal_text: Optional[str] = None

class MoodEntryUpdate(BaseModel):
    mood_score: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[List[str]] = None
    journal_text: Optional[str] = None

class MoodEntryResponse(BaseModel):
    id: UUID
    user_id: UUID
    mood_score: int
    tags: List[str]
    journal_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    can_edit: bool = True

    class Config:
        from_attributes = True
