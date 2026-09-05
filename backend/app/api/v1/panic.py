import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.alert import RiskAlert
from app.models.appointment import Appointment
from app.api.deps import get_current_user
from app.schemas.alert import PanicRequest, RiskAlertResponse

router = APIRouter()

@router.post("", response_model=RiskAlertResponse)
async def trigger_panic_sos(
    panic_in: PanicRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assigned_doc_id = panic_in.assigned_doctor_id

    # If no doctor assigned, check if user has an existing doctor from an appointment
    if not assigned_doc_id:
        appt_q = await db.execute(
            select(Appointment.doctor_id)
            .where(Appointment.patient_id == current_user.id, Appointment.doctor_id.isnot(None))
            .order_by(Appointment.created_at.desc())
        )
        assigned_doc_id = appt_q.scalars().first()

    # If still no doctor assigned, pick any active doctor
    if not assigned_doc_id:
        doc_q = await db.execute(
            select(User.id).where(User.role == "doctor", User.is_active == True)
        )
        assigned_doc_id = doc_q.scalars().first()

    sla_mins = panic_in.sla_minutes if panic_in.sla_minutes is not None else 15
    now = datetime.utcnow()
    sla_due = now + timedelta(minutes=sla_mins)

    history = [{
        "timestamp": now.isoformat(),
        "from_tier": 0,
        "to_tier": 1,
        "reason": f"Panic SOS triggered. Tier 1 primary doctor assigned with {sla_mins}-minute response SLA."
    }]

    alert = RiskAlert(
        user_id=current_user.id,
        severity="CRITICAL",
        trigger_source="panic_sos",
        details=f"One-Tap Panic SOS Triggered. Location Note: {panic_in.location_note or 'Platform Default'}",
        assigned_doctor_id=assigned_doc_id,
        sla_minutes=sla_mins,
        sla_due_at=sla_due,
        sla_breached=False,
        escalation_tier=1,
        escalation_history=json.dumps(history)
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    from app.services.notification_service import dispatch_critical_notifications
    await dispatch_critical_notifications(db, alert, current_user)
    await db.refresh(alert)
    return alert
