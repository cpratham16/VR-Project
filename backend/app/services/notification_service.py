from datetime import datetime, timedelta
import logging
from sqlalchemy import func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment
from app.models.notification import NotificationRecord

logger = logging.getLogger("app.notifications")


async def resolve_assigned_doctor(db: AsyncSession, patient: User, preferred_doctor_id=None):
    """Shared doctor-resolution cascade: explicit -> last appointment -> any active doctor."""
    if preferred_doctor_id:
        row = (
            await db.execute(
                select(User).where(
                    User.id == preferred_doctor_id,
                    User.role == "doctor",
                    User.is_active == True,
                )
            )
        ).scalars().first()
        if row:
            return row.id

    appt_q = await db.execute(
        select(Appointment.doctor_id)
        .where(Appointment.patient_id == patient.id, Appointment.doctor_id.isnot(None))
        .order_by(Appointment.created_at.desc())
    )
    from_appointment = appt_q.scalars().first()
    if from_appointment:
        return from_appointment

    doc_q = await db.execute(select(User.id).where(User.role == "doctor", User.is_active == True))
    return doc_q.scalars().first()


async def _on_call_pool(db: AsyncSession, patient: User):
    """Verified doctors matching the patient's state; falls back to all verified doctors."""
    pool = []
    if patient.state:
        pool = (
            await db.execute(
                select(User)
                .join(DoctorProfile, DoctorProfile.user_id == User.id)
                .where(
                    User.role == "doctor",
                    User.is_active == True,
                    User.is_verified == True,
                    DoctorProfile.credential_filename.isnot(None),
                    User.state == patient.state,
                )
            )
        ).scalars().all()
    if not pool:
        pool = (
            await db.execute(
                select(User)
                .join(DoctorProfile, DoctorProfile.user_id == User.id)
                .where(
                    User.role == "doctor",
                    User.is_active == True,
                    User.is_verified == True,
                    DoctorProfile.credential_filename.isnot(None),
                )
            )
        ).scalars().all()
    return pool


def _preview(alert) -> str:
    trigger = alert.trigger_source.replace("_", " ").upper()
    base = f"[{trigger}] High-risk alert ({alert.severity}) raised"
    details = (alert.details or "")[:140]
    return f"{base}. {details}"


async def _create_record(db: AsyncSession, alert, recipient_type: str, label: str | None, channel: str = "sms"):
    record = NotificationRecord(
        alert_id=alert.id,
        recipient_type=recipient_type,
        recipient_label=label,
        channel=channel,
        status="sent" if settings.NOTIFICATIONS_ENABLED else "simulated",
        content_preview=_preview(alert),
    )
    db.add(record)
    return record


async def dispatch_critical_notifications(db: AsyncSession, alert, patient: User) -> list[NotificationRecord]:
    """Parallel notification to the secondary emergency contact and the state's
    on-call doctor pool for a CRITICAL risk signal. Delivery is simulated via
    audit rows until a real provider is configured (G6)."""
    records: list[NotificationRecord] = []

    if patient.emergency_contact_phone:
        records.append(await _create_record(db, alert, "secondary_contact", patient.emergency_contact_phone))

    pool = await _on_call_pool(db, patient)
    for doc in pool:
        records.append(await _create_record(db, alert, "on_call_doctor", doc.email, channel="email"))

    if records:
        await db.commit()

    logger.info(
        "Crisis notifications dispatched for alert %s: %d recipients (%s)",
        alert.id, len(records), "live" if settings.NOTIFICATIONS_ENABLED else "simulated",
    )
    return records


async def record_backup_pool_notification(db: AsyncSession, alert) -> NotificationRecord:
    """Tier-2 escalation backup-pool notification record (extends D6 paths)."""
    record = await _create_record(db, alert, "backup_pool", "on-call backup doctor pool", channel="email")
    await db.commit()
    await db.refresh(record)
    return record


async def dispatch_content_notification(
    db: AsyncSession,
    title: str,
    content_type: str,  # "resource" | "newsletter" | "announcement"
    link_url: str,
    recipient_role: str = "patient"
) -> NotificationRecord:
    """Generates an in-app notification trigger for new published content (N7)."""
    record = NotificationRecord(
        alert_id=None,
        recipient_type=f"{content_type}_announcement",
        recipient_label=f"All {recipient_role}s",
        channel="in_app",
        status="sent",
        content_preview=f"New {content_type.capitalize()} Published: {title}",
        link_url=link_url
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


def attach_sla(alert, sla_minutes: int = 15):
    now = datetime.utcnow()
    alert.sla_minutes = sla_minutes
    alert.sla_due_at = now + timedelta(minutes=sla_minutes)
    alert.escalation_tier = max(alert.escalation_tier or 1, 1)
    if not alert.escalation_history:
        import json
        alert.escalation_history = json.dumps([{
            "timestamp": now.isoformat(),
            "from_tier": 0,
            "to_tier": 1,
            "reason": f"CRITICAL risk signal detected. {sla_minutes}-minute response SLA started.",
        }])
