import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytest
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.alert import RiskAlert
from app.models.notification import NotificationRecord
from app.schemas.chat import ChatMessageCreate
from app.api.v1.chat import send_chat_message
from app.api.v1.panic import trigger_panic_sos
from app.api.v1.screening import submit_screening
from app.schemas.alert import PanicRequest
from app.schemas.screening import ScreeningSubmission
from app.services.escalation_service import evaluate_alert_escalations


async def _make_patient(state="Maharashtra", city="Pune", emergency="+919800000001"):
    pid = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        user = User(
            id=pid,
            email=f"g6_pat_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="pw",
            role="patient",
            state=state,
            city=city,
            emergency_contact_phone=emergency,
        )
        db.add(user)
        await db.commit()
    return user


async def _make_oncall_doctor(state="Maharashtra", n=1):
    ids = []
    async with AsyncSessionLocal() as db:
        for _ in range(n):
            did = uuid.uuid4()
            user = User(
                id=did,
                email=f"g6_doc_{uuid.uuid4().hex[:6]}@test.com",
                hashed_password="pw",
                role="doctor",
                is_verified=True,
                state=state,
            )
            db.add(user)
            ids.append(did)
        await db.flush()
        for did in ids:
            db.add(DoctorProfile(
                user_id=did,
                license_number=f"LIC-{uuid.uuid4().hex[:8].upper()}",
                languages='["English"]',
                credential_filename="test-credential.pdf",
                review_status="approved",
            ))
        await db.commit()
    return ids


async def _cleanup(user_ids):
    from sqlalchemy import text
    async with AsyncSessionLocal() as db:
        await db.execute(text(
            "DELETE FROM notification_records WHERE alert_id IN "
            "(SELECT id FROM risk_alerts WHERE user_id = ANY(:ids))"
        ), {"ids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM chat_messages WHERE session_id IN "
            "(SELECT id FROM chat_sessions WHERE user_id = ANY(:ids))"
        ), {"ids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM chat_sessions WHERE user_id = ANY(:ids)"
        ), {"ids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM doctor_profiles WHERE user_id = ANY(:ids)"
        ), {"ids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM screening_results WHERE user_id = ANY(:ids)"
        ), {"ids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM risk_alerts WHERE user_id = ANY(:ids)"
        ), {"ids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM users WHERE id = ANY(:ids)"
        ), {"ids": list(user_ids)})
        await db.commit()


def _mock_llm():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "I hear you. You are not alone â€” help is available."}}]
    }
    return patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response)


@pytest.mark.asyncio
async def test_critical_chat_triggers_sla_and_parallel_notifications():
    patient = await _make_patient()
    doctor_ids = await _make_oncall_doctor("Maharashtra", n=2)

    async with AsyncSessionLocal() as db:
        patient_ref = await db.merge(patient)
        with _mock_llm():
            res = await send_chat_message(
                msg_in=ChatMessageCreate(message="I want to end my life tonight"),
                db=db,
                current_user=patient_ref,
            )
        assert res.id is not None

        alert = (
            await db.execute(
                select(RiskAlert)
                .where(RiskAlert.user_id == patient.id, RiskAlert.trigger_source == "chat_distress")
                .order_by(RiskAlert.created_at.desc())
            )
        ).scalars().first()

        assert alert is not None
        assert alert.severity == "CRITICAL"
        assert alert.assigned_doctor_id is not None, "CRITICAL chat flag must assign a doctor"
        assert alert.sla_due_at is not None, "CRITICAL chat flag must start the SLA window"
        assert datetime.utcnow() < alert.sla_due_at <= datetime.utcnow() + timedelta(minutes=16)

        records = (
            await db.execute(
                select(NotificationRecord).where(NotificationRecord.alert_id == alert.id)
            )
        ).scalars().all()

        types = sorted(r.recipient_type for r in records)
        assert types.count("on_call_doctor") >= 2, "state on-call doctors notified"
        assert "secondary_contact" in types, "secondary emergency contact notified"

        async with AsyncSessionLocal() as db2:
            our_doctors = (
                await db2.execute(select(User).where(User.id.in_(doctor_ids)))
            ).scalars().all()
        labels = [r.recipient_label for r in records if r.recipient_type == "on_call_doctor"]
        for doc in our_doctors:
            assert doc.email in labels, f"on-call doctor {doc.email} must be notified"

        secondary = next(r for r in records if r.recipient_type == "secondary_contact")
        assert secondary.recipient_label == "+919800000001"
        assert all(r.status == "simulated" for r in records)

    await _cleanup([patient.id] + doctor_ids)


@pytest.mark.asyncio
async def test_high_severity_flag_does_not_dispatch():
    patient = await _make_patient(emergency=None)

    async with AsyncSessionLocal() as db:
        patient_ref = await db.merge(patient)
        with _mock_llm():
            await send_chat_message(
                msg_in=ChatMessageCreate(message="I am having an extreme panic attack right now"),
                db=db,
                current_user=patient_ref,
            )

        alert = (
            await db.execute(
                select(RiskAlert).where(RiskAlert.user_id == patient.id)
            )
        ).scalars().first()
        assert alert is not None
        assert alert.severity == "HIGH"
        assert alert.sla_due_at is None

        records = (
            await db.execute(
                select(NotificationRecord).where(NotificationRecord.alert_id == alert.id)
            )
        ).scalars().all()
        assert len(records) == 0, "only CRITICAL signals dispatch notifications"

    await _cleanup([patient.id])


@pytest.mark.asyncio
async def test_panic_sos_and_screening_critical_dispatch():
    patient = await _make_patient()
    doctor_ids = await _make_oncall_doctor("Maharashtra", n=1)

    async with AsyncSessionLocal() as db:
        patient_ref = await db.merge(patient)
        sos = await trigger_panic_sos(panic_in=PanicRequest(location_note="Test"), db=db, current_user=patient_ref)

        sos_records = (
            await db.execute(
                select(NotificationRecord).where(NotificationRecord.alert_id == sos.id)
            )
        ).scalars().all()
        assert len(sos_records) >= 2  # secondary contact + on-call doctor

        critical_answers = [0, 0, 0, 0, 0, 0, 0, 0, 1]
        await submit_screening(
            submission=ScreeningSubmission(screening_type="PHQ-9", answers=critical_answers),
            db=db,
            current_user=patient_ref,
        )

        screen_alert = (
            await db.execute(
                select(RiskAlert)
                .where(RiskAlert.user_id == patient.id, RiskAlert.trigger_source == "screening_high")
                .order_by(RiskAlert.created_at.desc())
            )
        ).scalars().first()
        assert screen_alert is not None
        assert screen_alert.severity == "CRITICAL"
        assert screen_alert.sla_due_at is not None

        screen_records = (
            await db.execute(
                select(NotificationRecord).where(NotificationRecord.alert_id == screen_alert.id)
            )
        ).scalars().all()
        assert len(screen_records) >= 2

    await _cleanup([patient.id] + doctor_ids)


@pytest.mark.asyncio
async def test_tier2_escalation_creates_backup_pool_notification():
    patient = await _make_patient()

    async with AsyncSessionLocal() as db:
        alert = RiskAlert(
            user_id=patient.id,
            severity="CRITICAL",
            trigger_source="panic_sos",
            details="G6 tier test",
            sla_minutes=15,
            sla_due_at=datetime.utcnow() - timedelta(minutes=1),
            escalation_tier=1,
        )
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        escalated = await evaluate_alert_escalations(db)
        target = next(a for a in escalated if a.id == alert.id)
        assert target.escalation_tier == 2

        backup_records = (
            await db.execute(
                select(NotificationRecord).where(
                    NotificationRecord.alert_id == alert.id,
                    NotificationRecord.recipient_type == "backup_pool",
                )
            )
        ).scalars().all()
        assert len(backup_records) == 1

    await _cleanup([patient.id])
