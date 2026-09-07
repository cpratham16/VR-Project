from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class NewsletterBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    author: Optional[str] = None
    is_published: bool = False

class NewsletterCreate(NewsletterBase):
    pass

class NewsletterUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    is_published: Optional[bool] = None

class NewsletterResponse(NewsletterBase):
    id: str
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
