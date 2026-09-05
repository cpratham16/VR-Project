import pytest
import uuid
import json
from datetime import datetime, timedelta
from app.models.user import User
from app.models.alert import RiskAlert
from app.core.database import AsyncSessionLocal
from app.schemas.alert import PanicRequest, AcknowledgeAlertRequest, EscalateAlertRequest
from app.api.v1.panic import trigger_panic_sos
from app.api.v1.doctor_alerts import get_doctor_alerts, acknowledge_alert, check_and_escalate_alerts, escalate_alert
from app.services.escalation_service import evaluate_alert_escalations, manual_escalate_alert
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_panic_sos_and_multi_tier_escalation_pipeline():
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        patient = User(id=patient_id, email=f"pat_panic_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient")
        doctor = User(id=doctor_id, email=f"doc_panic_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="doctor")
        db.add_all([patient, doctor])
        await db.commit()

        # 1. Trigger Panic SOS (Tier 1)
        req = PanicRequest(location_note="Library Study Room 4", sla_minutes=15, assigned_doctor_id=doctor_id)
        alert_res = await trigger_panic_sos(panic_in=req, db=db, current_user=patient)

        assert alert_res.severity == "CRITICAL"
        assert alert_res.escalation_tier == 1
        assert alert_res.sla_minutes == 15
        assert alert_res.sla_due_at is not None
        assert alert_res.sla_breached is False
        assert alert_res.assigned_doctor_id == doctor_id

        # Check escalation history
        history = json.loads(alert_res.escalation_history)
        assert len(history) == 1
        assert history[0]["to_tier"] == 1

        # 2. Simulate SLA Breach Tier 1 -> Tier 2 (Backup On-Call Doctor Pool)
        db_alert = (await db.execute(select(RiskAlert).where(RiskAlert.id == alert_res.id))).scalars().first()
        db_alert.sla_due_at = datetime.utcnow() - timedelta(minutes=1)
        await db.commit()

        escalated_alerts = await evaluate_alert_escalations(db)
        tier2_alert = next(a for a in escalated_alerts if a.id == alert_res.id)
        assert tier2_alert.escalation_tier == 2
        assert tier2_alert.sla_breached is True
        assert "Backup Pool" in tier2_alert.details

        # 3. Simulate Second SLA Breach Tier 2 -> Tier 3 (Crisis Hotline 988 / Security)
        tier2_alert.sla_due_at = datetime.utcnow() - timedelta(minutes=1)
        await db.commit()

        escalated_tier3 = await evaluate_alert_escalations(db)
        tier3_alert = next(a for a in escalated_tier3 if a.id == alert_res.id)
        assert tier3_alert.escalation_tier == 3
        assert "Crisis Hotline 988" in tier3_alert.details

        # Verify history has 3 entries (0->1, 1->2, 2->3)
        history_final = json.loads(tier3_alert.escalation_history)
        assert len(history_final) == 3
        assert history_final[2]["to_tier"] == 3

        # 4. Doctor Acknowledgment
        ack_req = AcknowledgeAlertRequest(resolution_notes="Patient contacted and in safe care with campus staff.")
        ack_res = await acknowledge_alert(alert_id=str(tier3_alert.id), req_in=ack_req, db=db, current_doctor=doctor)
        assert ack_res["status"] == "acknowledged"
        assert ack_res["acknowledged_by_doctor_id"] == doctor_id

        # Cleanup
        db_alert_clean = (await db.execute(select(RiskAlert).where(RiskAlert.id == alert_res.id))).scalars().first()
        from sqlalchemy import delete as _delete
        from app.models.notification import NotificationRecord as _NR
        await db.execute(_delete(_NR).where(_NR.alert_id == db_alert_clean.id))
        await db.delete(db_alert_clean)
        await db.delete(patient)
        await db.delete(doctor)
        await db.commit()

@pytest.mark.asyncio
async def test_manual_escalation_endpoint():
    patient_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        patient = User(id=patient_id, email=f"pat_panic_man_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="patient")
        doctor = User(id=doctor_id, email=f"doc_panic_man_{uuid.uuid4().hex[:6]}@test.com", hashed_password="pw", role="doctor")
        db.add_all([patient, doctor])
        await db.commit()

        req = PanicRequest(location_note="Dorm Hall B")
        alert_res = await trigger_panic_sos(panic_in=req, db=db, current_user=patient)

        # Doctor manually escalates alert
        esc_req = EscalateAlertRequest(reason="Immediate secondary risk identified in intake text")
        esc_res = await escalate_alert(alert_id=str(alert_res.id), req_in=esc_req, db=db, current_doctor=doctor)

        assert esc_res["escalation_tier"] == 2
        assert esc_res["sla_breached"] is True
        assert "MANUALLY ESCALATED" in esc_res["details"]

        # Cleanup
        db_alert = (await db.execute(select(RiskAlert).where(RiskAlert.id == alert_res.id))).scalars().first()
        from sqlalchemy import delete as _delete2
        from app.models.notification import NotificationRecord as _NR2
        await db.execute(_delete2(_NR2).where(_NR2.alert_id == db_alert.id))
        await db.delete(db_alert)
        await db.delete(patient)
        await db.delete(doctor)
        await db.commit()
