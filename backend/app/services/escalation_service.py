import json
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.alert import RiskAlert

async def evaluate_alert_escalations(db: AsyncSession) -> List[RiskAlert]:
    """
    Checks all pending risk alerts that have breached their response SLA time window.
    Escalates tiers:
      Tier 1 (Assigned doctor) -> Tier 2 (Backup on-call pool) -> Tier 3 (Crisis hotline 988 / Security)
    """
    now = datetime.utcnow()
    query = await db.execute(
        select(RiskAlert).where(
            RiskAlert.status == "pending",
            RiskAlert.escalation_tier < 3,
            RiskAlert.sla_due_at.isnot(None),
            RiskAlert.sla_due_at <= now
        )
    )
    alerts_to_escalate = query.scalars().all()

    escalated_alerts = []
    for alert in alerts_to_escalate:
        history = []
        if alert.escalation_history:
            try:
                history = json.loads(alert.escalation_history)
            except Exception:
                history = []

        old_tier = alert.escalation_tier
        if old_tier == 1:
            new_tier = 2
            alert.sla_breached = True
            alert.escalation_tier = new_tier
            # Extend SLA for on-call doctor pool response (e.g. +10 mins)
            alert.sla_due_at = now + timedelta(minutes=10)
            reason = "SLA breached by primary assigned doctor. Escalated to backup on-call doctor pool."
            alert.details += f" | [ESCALATED TO TIER 2: Backup Pool]"
        else:
            new_tier = 3
            alert.escalation_tier = new_tier
            alert.sla_due_at = None
            reason = "SLA breached by backup doctor pool. Dispatched to National Crisis Lifeline (988) & Emergency Dispatch."
            alert.details += f" | [ESCALATED TO TIER 3: Crisis Hotline 988 & Emergency Services Dispatched]"

        history.append({
            "timestamp": now.isoformat(),
            "from_tier": old_tier,
            "to_tier": new_tier,
            "reason": reason
        })
        alert.escalation_history = json.dumps(history)

        if new_tier == 2:
            from app.services.notification_service import record_backup_pool_notification
            await record_backup_pool_notification(db, alert)

        escalated_alerts.append(alert)

    if escalated_alerts:
        await db.commit()
        for alert in escalated_alerts:
            await db.refresh(alert)

    return escalated_alerts

async def manual_escalate_alert(db: AsyncSession, alert: RiskAlert, reason: str = "Manual escalation") -> RiskAlert:
    """
    Manually steps an alert up to the next escalation tier.
    """
    now = datetime.utcnow()
    history = []
    if alert.escalation_history:
        try:
            history = json.loads(alert.escalation_history)
        except Exception:
            history = []

    old_tier = alert.escalation_tier
    if old_tier < 3:
        new_tier = old_tier + 1
        alert.escalation_tier = new_tier
        alert.sla_breached = True
        if new_tier == 2:
            alert.sla_due_at = now + timedelta(minutes=10)
            alert.details += f" | [MANUALLY ESCALATED TO TIER 2: Backup Pool]"
        else:
            alert.sla_due_at = None
            alert.details += f" | [MANUALLY ESCALATED TO TIER 3: Crisis Hotline 988 & Emergency Services Dispatched]"

        history.append({
            "timestamp": now.isoformat(),
            "from_tier": old_tier,
            "to_tier": new_tier,
            "reason": f"Manual escalation: {reason}"
        })
        alert.escalation_history = json.dumps(history)
        await db.commit()
        await db.refresh(alert)

    return alert
