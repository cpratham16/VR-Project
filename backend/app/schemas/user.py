from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    role: str = "patient"

class UserCreate(UserBase):
    password: str
    state: Optional[str] = None
    city: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True
