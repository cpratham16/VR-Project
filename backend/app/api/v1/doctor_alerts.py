from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.alert import RiskAlert
from app.models.notification import NotificationRecord
from app.api.deps import get_current_doctor, get_current_verified_doctor
from app.schemas.alert import RiskAlertResponse, AcknowledgeAlertRequest, EscalateAlertRequest
from app.services.escalation_service import evaluate_alert_escalations, manual_escalate_alert

router = APIRouter()

async def _build_alert_dict(db: AsyncSession, alert: RiskAlert) -> dict:
    p_query = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == alert.user_id)
    )
    patient = p_query.scalars().first()
    pseudonym = patient.pseudonym if patient else "Anonymous Member"

    n_query = await db.execute(
        select(NotificationRecord).where(NotificationRecord.alert_id == alert.id)
    )
    notifications = n_query.scalars().all()

    return {
        "id": alert.id,
        "user_id": alert.user_id,
        "patient_pseudonym": pseudonym,
        "severity": alert.severity,
        "trigger_source": alert.trigger_source,
        "details": alert.details,
        "status": alert.status,
        "acknowledged_by_doctor_id": alert.acknowledged_by_doctor_id,
        "assigned_doctor_id": alert.assigned_doctor_id,
        "sla_minutes": alert.sla_minutes,
        "sla_due_at": alert.sla_due_at,
        "sla_breached": alert.sla_breached,
        "escalation_tier": alert.escalation_tier,
        "escalation_history": alert.escalation_history,
        "notification_count": len(notifications),
        "notification_recipients": [n.recipient_label or n.recipient_type for n in notifications],
        "created_at": alert.created_at,
        "resolved_at": alert.resolved_at
    }

@router.get("", response_model=List[RiskAlertResponse])
async def get_doctor_alerts(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    query = await db.execute(
        select(RiskAlert)
        .order_by(RiskAlert.created_at.desc())
    )
    alerts = query.scalars().all()

    response_list = []
    for alert in alerts:
        res = await _build_alert_dict(db, alert)
        response_list.append(res)

    return response_list

@router.post("/check-escalations", response_model=List[RiskAlertResponse])
async def check_and_escalate_alerts(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    escalated_alerts = await evaluate_alert_escalations(db)
    res_list = []
    for alert in escalated_alerts:
        res = await _build_alert_dict(db, alert)
        res_list.append(res)
    return res_list

@router.post("/{alert_id}/acknowledge", response_model=RiskAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    req_in: AcknowledgeAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
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

    return await _build_alert_dict(db, alert)

@router.post("/{alert_id}/escalate", response_model=RiskAlertResponse)
async def escalate_alert(
    alert_id: str,
    req_in: EscalateAlertRequest,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_verified_doctor)
):
    query = await db.execute(select(RiskAlert).where(RiskAlert.id == alert_id))
    alert = query.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    reason = req_in.reason or f"Manual escalation by Dr. {current_doctor.email}"
    alert = await manual_escalate_alert(db, alert, reason=reason)
    return await _build_alert_dict(db, alert)
