from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.alert import RiskAlert
from app.api.deps import get_current_doctor
from app.schemas.alert import RiskAlertResponse, AcknowledgeAlertRequest

router = APIRouter()

@router.get("", response_model=List[RiskAlertResponse])
async def get_doctor_alerts(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    query = await db.execute(
        select(RiskAlert)
        .order_by(RiskAlert.created_at.desc())
    )
    alerts = query.scalars().all()

    response_list = []
    for alert in alerts:
        p_query = await db.execute(
            select(PatientProfile).where(PatientProfile.user_id == alert.user_id)
        )
        patient = p_query.scalars().first()
        pseudonym = patient.pseudonym if patient else "Anonymous Student"

        response_list.append({
            "id": alert.id,
            "user_id": alert.user_id,
            "patient_pseudonym": pseudonym,
            "severity": alert.severity,
            "trigger_source": alert.trigger_source,
            "details": alert.details,
            "status": alert.status,
            "acknowledged_by_doctor_id": alert.acknowledged_by_doctor_id,
            "created_at": alert.created_at,
            "resolved_at": alert.resolved_at
        })

    return response_list

@router.post("/{alert_id}/acknowledge", response_model=RiskAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    req_in: AcknowledgeAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    query = await db.execute(select(RiskAlert).where(RiskAlert.id == alert_id))
    alert = query.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    alert.acknowledged_by_doctor_id = current_doctor.id
    alert.resolved_at = datetime.utcnow()
    if req_in.resolution_notes:
        alert.details += f" | Doctor Note: {req_in.resolution_notes}"

    await db.commit()
    await db.refresh(alert)

    p_query = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == alert.user_id)
    )
    patient = p_query.scalars().first()
    pseudonym = patient.pseudonym if patient else "Anonymous Student"

    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "patient_pseudonym": pseudonym,
        "severity": alert.severity,
        "trigger_source": alert.trigger_source,
        "details": alert.details,
        "status": alert.status,
        "acknowledged_by_doctor_id": alert.acknowledged_by_doctor_id,
        "created_at": alert.created_at,
        "resolved_at": alert.resolved_at
    }
