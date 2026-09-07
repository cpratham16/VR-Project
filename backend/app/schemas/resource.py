from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ResourceBase(BaseModel):
    title: str
    description: Optional[str] = None
    resource_type: str = "pdf"
    category: str = "general"
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    is_published: bool = False

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = None
    category: Optional[str] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    is_published: Optional[bool] = None

class ResourceResponse(ResourceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResourceProgressUpdate(BaseModel):
    saved_for_later: Optional[bool] = None
    progress_percent: Optional[int] = None
    is_completed: Optional[bool] = None

class ResourceProgressResponse(BaseModel):
    id: str
    resource_id: str
    saved_for_later: bool
    progress_percent: int
    is_completed: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResourceWithProgressResponse(ResourceResponse):
    progress: Optional[ResourceProgressResponse] = None
