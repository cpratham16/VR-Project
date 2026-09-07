from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_AUDIENCES = {"all", "students", "doctors", "admins"}

class CampaignBase(BaseModel):
    title: str
    subject: str
    body_html: str
    audience_type: str = "all"
    delivery_channels: str = "email,in_app"
    scheduled_at: Optional[datetime] = None

    @field_validator("audience_type")
    @classmethod
    def validate_audience(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in ALLOWED_AUDIENCES:
            raise ValueError(f"Invalid audience_type '{v}'. Targeting by clinical or non-demographic fields is prohibited. Allowed: {sorted(ALLOWED_AUDIENCES)}")
        return v_clean

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    audience_type: Optional[str] = None
    delivery_channels: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None

    @field_validator("audience_type")
    @classmethod
    def validate_audience(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip().lower()
        if v_clean not in ALLOWED_AUDIENCES:
            raise ValueError(f"Invalid audience_type '{v}'. Allowed: {sorted(ALLOWED_AUDIENCES)}")
        return v_clean

class RecipientResponse(BaseModel):
    id: str
    user_id: str
    email: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    @field_validator("user_id", mode="before")
    @classmethod
    def serialize_user_id(cls, v):
        return str(v) if v is not None else v

    model_config = ConfigDict(from_attributes=True)

class CampaignResponse(CampaignBase):
    id: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    recipient_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class CampaignDetailResponse(CampaignResponse):
    recipients: List[RecipientResponse] = []

class UnsubscribeUpdate(BaseModel):
    unsubscribed: bool
