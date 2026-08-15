from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PatientProfileBase(BaseModel):
    pseudonym: str

class PatientProfileCreate(PatientProfileBase):
    pass

class PatientProfileResponse(PatientProfileBase):
    id: UUID
    user_id: UUID
    
    class Config:
        from_attributes = True

class ConsentRecordBase(BaseModel):
    consent_version: str
    agreed_to_ai_processing: bool
    agreed_to_data_usage: bool

class ConsentRecordCreate(ConsentRecordBase):
    pass

class ConsentRecordResponse(ConsentRecordBase):
    id: UUID
    user_id: UUID
    agreed_at: datetime
    
    class Config:
        from_attributes = True

class PatientOnboardingStatus(BaseModel):
    has_profile: bool
    has_consent: bool
    latest_consent_version: Optional[str] = None
