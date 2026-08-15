from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.vr import VRScenario, VRSession, VRTelemetry
from app.api.deps import get_current_doctor
from app.schemas.vr import (
    VRScenarioResponse,
    VRAssignmentCreate,
    VRSessionResponse,
    VRTelemetryResponse,
    VRAssignmentCancel,
)

router = APIRouter()

def _serialize_session(session: VRSession, scenario: Optional[VRScenario]) -> dict:
    return {
        "id": session.id,
        "patient_id": session.patient_id,
        "doctor_id": session.doctor_id,
        "scenario_id": session.scenario_id,
        "scenario_name": scenario.name if scenario else "",
        "scenario_slug": scenario.slug if scenario else "",
        "phobia_type": scenario.phobia_type if scenario else "",
        "intensity_level": session.intensity_level,
        "duration_minutes": session.duration_minutes,
        "exposure_steps": session.exposure_steps,
        "instructions": session.instructions,
        "status": session.status,
        "suds_pre": session.suds_pre,
        "suds_post": session.suds_post,
        "patient_feedback": session.patient_feedback,
        "assigned_at": session.assigned_at,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
    }

@router.get("/scenarios", response_model=List[VRScenarioResponse])
async def list_vr_scenarios(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    query = await db.execute(select(VRScenario).where(VRScenario.is_active == True))
    return query.scalars().all()

@router.post("/assign", response_model=VRSessionResponse)
async def assign_vr_session(
    assign_in: VRAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    # Validate patient exists and is a patient role
    patient_q = await db.execute(select(User).where(User.id == assign_in.patient_id))
    patient = patient_q.scalars().first()
    if not patient or patient.role != "patient":
        raise HTTPException(status_code=404, detail="Patient not found")

    scenario_q = await db.execute(
        select(VRScenario).where(VRScenario.id == assign_in.scenario_id)
    )
    scenario = scenario_q.scalars().first()
    if not scenario or not scenario.is_active:
        raise HTTPException(status_code=404, detail="VR scenario not found")

    session = VRSession(
        patient_id=assign_in.patient_id,
        doctor_id=current_doctor.id,
        scenario_id=assign_in.scenario_id,
        intensity_level=assign_in.intensity_level,
        duration_minutes=assign_in.duration_minutes,
        exposure_steps=assign_in.exposure_steps,
        instructions=assign_in.instructions,
        status="assigned",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _serialize_session(session, scenario)

@router.get("/sessions", response_model=List[VRSessionResponse])
async def list_patient_vr_sessions(
    patient_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    query = select(VRSession)
    if patient_id:
        query = query.where(VRSession.patient_id == patient_id)
    query = query.order_by(VRSession.assigned_at.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()

    # Load scenario names for serialization
    scenario_map = {}
    scenario_q = await db.execute(select(VRScenario))
    for s in scenario_q.scalars().all():
        scenario_map[s.id] = s

    return [_serialize_session(s, scenario_map.get(s.scenario_id)) for s in sessions]

@router.get("/sessions/{session_id}/telemetry", response_model=List[VRTelemetryResponse])
async def get_session_telemetry(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    result = await db.execute(
        select(VRTelemetry)
        .where(VRTelemetry.session_id == session_id)
        .order_by(VRTelemetry.timestamp.asc())
    )
    return result.scalars().all()

@router.post("/sessions/{session_id}/cancel", response_model=VRSessionResponse)
async def cancel_vr_session(
    session_id: str,
    cancel_in: VRAssignmentCancel,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor),
):
    query = await db.execute(select(VRSession).where(VRSession.id == session_id))
    session = query.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="VR session not found")

    if session.status not in ("assigned", "in_progress"):
        raise HTTPException(status_code=400, detail="Session already closed")

    session.status = "cancelled"
    if cancel_in.reason:
        session.patient_feedback = f"[Cancelled by doctor] {cancel_in.reason}"

    await db.commit()
    await db.refresh(session)

    scenario_q = await db.execute(select(VRScenario).where(VRScenario.id == session.scenario_id))
    scenario = scenario_q.scalars().first()
    return _serialize_session(session, scenario)
