from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class PanicRequest(BaseModel):
    location_note: Optional[str] = "Platform Default"
    sla_minutes: Optional[int] = 15
    assigned_doctor_id: Optional[UUID] = None

class RiskAlertResponse(BaseModel):
    id: UUID
    user_id: UUID
    patient_pseudonym: Optional[str] = "Anonymous Member"
    severity: str
    trigger_source: str
    details: str
    status: str
    acknowledged_by_doctor_id: Optional[UUID] = None
    assigned_doctor_id: Optional[UUID] = None
    sla_minutes: int = 15
    sla_due_at: Optional[datetime] = None
    sla_breached: bool = False
    escalation_tier: int = 1
    escalation_history: Optional[str] = None
    notification_count: int = 0
    notification_recipients: List[str] = []
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class AcknowledgeAlertRequest(BaseModel):
    resolution_notes: Optional[str] = None

class EscalateAlertRequest(BaseModel):
    reason: Optional[str] = "Manual escalation requested by clinician"
