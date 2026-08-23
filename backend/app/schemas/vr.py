from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class VRScenarioResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    phobia_type: str
    description: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class VRAssignmentCreate(BaseModel):
    patient_id: UUID
    scenario_id: UUID
    intensity_level: str = Field(default="medium", pattern="^(low|medium|high)$")
    duration_minutes: int = Field(default=10, ge=2, le=60)
    exposure_steps: int = Field(default=5, ge=2, le=10)
    instructions: str = Field(default="", max_length=1000)

class VRSessionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    scenario_id: UUID
    scenario_name: str = ""
    scenario_slug: str = ""
    phobia_type: str = ""
    intensity_level: str
    duration_minutes: int
    exposure_steps: int
    instructions: str
    status: str
    suds_pre: Optional[int] = None
    suds_post: Optional[int] = None
    patient_feedback: Optional[str] = None
    time_in_scene: Optional[float] = None
    interaction_count: Optional[int] = 0
    completion_status: Optional[str] = None
    assigned_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class VRTelemetryCreate(BaseModel):
    heart_rate: Optional[float] = None
    hrv_rmssd: Optional[float] = None
    stress_index: Optional[float] = None
    scene_stage: int = Field(default=1, ge=1)

class VRTelemetryResponse(BaseModel):
    id: UUID
    session_id: UUID
    timestamp: datetime
    heart_rate: Optional[float] = None
    hrv_rmssd: Optional[float] = None
    stress_index: Optional[float] = None
    scene_stage: int

    model_config = ConfigDict(from_attributes=True)

class VRCompletionCreate(BaseModel):
    suds_pre: int = Field(ge=1, le=10)
    suds_post: int = Field(ge=1, le=10)
    patient_feedback: Optional[str] = Field(default="", max_length=2000)
    time_in_scene: Optional[float] = None
    interaction_count: Optional[int] = 0
    completion_status: Optional[str] = "completed_fully"

class VRAssignmentCancel(BaseModel):
    reason: Optional[str] = Field(default="", max_length=500)
