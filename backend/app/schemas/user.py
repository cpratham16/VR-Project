from typing import Optional, List
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    role: str = "patient"

class UserCreate(UserBase):
    password: str
    state: Optional[str] = None
    city: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    languages: Optional[List[str]] = None

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    state: Optional[str] = None
    city: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    has_credentials: bool = False
    review_status: str = "approved"
    rejection_reason: Optional[str] = None
    specialty: Optional[str] = None
    languages: Optional[List[str]] = None

    class Config:
        from_attributes = True


class AdminCreate(BaseModel):
    """Provision a new administrator account (admin-only endpoint)."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    specialty: Optional[str] = None
    languages: Optional[List[str]] = None
