from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.vr import VRScenario, VRSession, VRTelemetry
from app.api.deps import get_current_user
from app.schemas.vr import (
    VRSessionResponse,
    VRTelemetryCreate,
    VRTelemetryResponse,
    VRCompletionCreate,
)
from app.services.vr_engine import calculate_stress_index

router = APIRouter()

def _serialize_session(session: VRSession, scenario) -> dict:
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

@router.get("/assigned", response_model=List[VRSessionResponse])
async def get_assigned_vr_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = await db.execute(
        select(VRSession)
        .where(VRSession.patient_id == current_user.id)
        .order_by(VRSession.assigned_at.desc())
    )
    sessions = query.scalars().all()

    scenario_map = {}
    scenario_q = await db.execute(select(VRScenario))
    for s in scenario_q.scalars().all():
        scenario_map[s.id] = s

    return [_serialize_session(s, scenario_map.get(s.scenario_id)) for s in sessions]

@router.post("/sessions/{session_id}/start", response_model=VRSessionResponse)
async def start_vr_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = await db.execute(select(VRSession).where(VRSession.id == session_id))
    session = query.scalars().first()
    if not session or session.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="VR session not found")

    if session.status == "completed" or session.status == "cancelled":
        raise HTTPException(status_code=400, detail="Session already closed")

    session.status = "in_progress"
    session.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)

    scenario_q = await db.execute(select(VRScenario).where(VRScenario.id == session.scenario_id))
    scenario = scenario_q.scalars().first()
    return _serialize_session(session, scenario)

@router.post("/sessions/{session_id}/telemetry", response_model=VRTelemetryResponse)
async def upload_telemetry(
    session_id: str,
    telemetry_in: VRTelemetryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = await db.execute(select(VRSession).where(VRSession.id == session_id))
    session = query.scalars().first()
    if not session or session.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="VR session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    stress_index = telemetry_in.stress_index
    if stress_index is None:
        stress_index = calculate_stress_index(telemetry_in.heart_rate, telemetry_in.hrv_rmssd)

    telemetry = VRTelemetry(
        session_id=session.id,
        heart_rate=telemetry_in.heart_rate,
        hrv_rmssd=telemetry_in.hrv_rmssd,
        stress_index=stress_index,
        scene_stage=telemetry_in.scene_stage,
    )
    db.add(telemetry)
    await db.commit()
    await db.refresh(telemetry)
    return telemetry

@router.post("/sessions/{session_id}/complete", response_model=VRSessionResponse)
async def complete_vr_session(
    session_id: str,
    complete_in: VRCompletionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = await db.execute(select(VRSession).where(VRSession.id == session_id))
    session = query.scalars().first()
    if not session or session.patient_id != current_user.id:
        raise HTTPException(status_code=404, detail="VR session not found")
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="Session is not in progress")

    session.status = "completed"
    session.completed_at = datetime.utcnow()
    session.suds_pre = complete_in.suds_pre
    session.suds_post = complete_in.suds_post
    session.patient_feedback = complete_in.patient_feedback or ""
    await db.commit()
    await db.refresh(session)

    scenario_q = await db.execute(select(VRScenario).where(VRScenario.id == session.scenario_id))
    scenario = scenario_q.scalars().first()
    return _serialize_session(session, scenario)
