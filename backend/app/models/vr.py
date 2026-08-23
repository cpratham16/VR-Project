import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class VRScenario(Base):
    __tablename__ = "vr_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)  # "heights", "public_speaking"
    name = Column(String, nullable=False)
    phobia_type = Column(String, nullable=False)  # "acrophobia", "glossophobia"
    description = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class VRSession(Base):
    __tablename__ = "vr_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("vr_scenarios.id"), nullable=False)
    intensity_level = Column(String, default="medium", nullable=False)  # "low", "medium", "high"
    duration_minutes = Column(Integer, default=10, nullable=False)
    exposure_steps = Column(Integer, default=5, nullable=False)
    instructions = Column(Text, default="", nullable=False)
    status = Column(String, default="assigned", nullable=False)  # "assigned", "in_progress", "completed", "cancelled"
    suds_pre = Column(Integer, nullable=True)  # 1-10
    suds_post = Column(Integer, nullable=True)  # 1-10
    patient_feedback = Column(Text, nullable=True)
    time_in_scene = Column(Float, nullable=True)     # Engagement: time spent running sec
    interaction_count = Column(Integer, default=0)   # Engagement: clicks/actions
    completion_status = Column(String, nullable=True)# e.g. "completed_fully", "exited_early"
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

class VRTelemetry(Base):
    __tablename__ = "vr_telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("vr_sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    heart_rate = Column(Float, nullable=True)  # bpm
    hrv_rmssd = Column(Float, nullable=True)  # ms
    stress_index = Column(Float, nullable=True)  # 0-100
    scene_stage = Column(Integer, default=1, nullable=False)
