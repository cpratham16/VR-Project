import uuid
import pytest
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.vr import VRScenario, VRSession, VRTelemetry
from app.schemas.vr import (
    VRSelfInitiateCreate,
    VRTelemetryCreate,
    VRCompletionCreate,
    VRAssignmentCreate,
)
from app.api.v1.patient_vr import (
    list_available_scenarios,
    self_initiate_session,
    start_vr_session,
    upload_telemetry,
    complete_vr_session,
)
from app.api.v1.doctor_vr import assign_vr_session, list_patient_vr_sessions


async def _make_user(role: str) -> User:
    uid = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        user = User(
            id=uid,
            email=f"g7_{role}_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="pw",
            role=role,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        db.expunge(user)
    return user


async def _make_scenario(slug_suffix: str) -> VRScenario:
    async with AsyncSessionLocal() as db:
        scenario = VRScenario(
            slug=f"g7_test_{slug_suffix}_{uuid.uuid4().hex[:6]}",
            name="G7 Test Scenario",
            phobia_type="acrophobia",
            description="Test scenario for access-model change.",
            is_active=True,
        )
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)
        db.expunge(scenario)
    return scenario


async def _cleanup(user_ids, scenario_ids):
    from sqlalchemy import text
    async with AsyncSessionLocal() as db:
        await db.execute(text(
            "DELETE FROM vr_telemetry WHERE session_id IN "
            "(SELECT id FROM vr_sessions WHERE patient_id = ANY(:uids))"
        ), {"uids": list(user_ids)})
        await db.execute(text(
            "DELETE FROM vr_sessions WHERE patient_id = ANY(:uids)"
        ), {"uids": list(user_ids)})
        await db.execute(text("DELETE FROM users WHERE id = ANY(:uids)"), {"uids": list(user_ids)})
        await db.execute(text("DELETE FROM vr_scenarios WHERE id = ANY(:sids)"), {"sids": list(scenario_ids)})
        await db.commit()


@pytest.mark.asyncio
async def test_patient_browse_and_complete_vr_without_doctor():
    patient = await _make_user("patient")
    scenario = await _make_scenario("browse")

    async with AsyncSessionLocal() as db:
        catalog = await list_available_scenarios(db=db, current_user=patient)
        assert any(str(s.id) == str(scenario.id) for s in catalog)

        initiated = await self_initiate_session(
            initiate_in=VRSelfInitiateCreate(scenario_id=scenario.id, intensity_level="medium"),
            db=db,
            current_user=patient,
        )
        assert initiated["doctor_id"] is None
        assert initiated["source"] == "self_initiated"
        assert initiated["status"] == "assigned"
        assert initiated["duration_minutes"] == 10
        assert initiated["exposure_steps"] == 3

        started = await start_vr_session(session_id=str(initiated["id"]), db=db, current_user=patient)
        assert started["status"] == "in_progress"

        tele = await upload_telemetry(
            session_id=str(initiated["id"]),
            telemetry_in=VRTelemetryCreate(heart_rate=95.0, hrv_rmssd=42.0, scene_stage=2),
            db=db,
            current_user=patient,
        )
        assert tele.session_id is not None

        finished = await complete_vr_session(
            session_id=str(initiated["id"]),
            complete_in=VRCompletionCreate(suds_pre=6, suds_post=3, patient_feedback="Felt calmer"),
            db=db,
            current_user=patient,
        )
        assert finished["status"] == "completed"
        assert finished["suds_pre"] == 6
        assert finished["suds_post"] == 3

    await _cleanup([patient.id], [scenario.id])


@pytest.mark.asyncio
async def test_doctor_report_includes_self_initiated_and_assignment_regression():
    patient = await _make_user("patient")
    doctor = await _make_user("doctor")
    scenario_a = await _make_scenario("report")
    scenario_b = await _make_scenario("assign")

    async with AsyncSessionLocal() as db:
        patient_ref = await db.merge(patient)
        doctor_ref = await db.merge(doctor)

        initiated = await self_initiate_session(
            initiate_in=VRSelfInitiateCreate(scenario_id=scenario_a.id, intensity_level="low"),
            db=db,
            current_user=patient_ref,
        )

        assigned = await assign_vr_session(
            assign_in=VRAssignmentCreate(
                patient_id=patient.id,
                scenario_id=scenario_b.id,
                intensity_level="high",
                instructions="Weekly exposure homework",
            ),
            db=db,
            current_doctor=doctor_ref,
        )
        assert assigned["source"] == "assigned"
        assert str(assigned["doctor_id"]) == str(doctor.id)

        report = await list_patient_vr_sessions(db=db, patient_id=None, current_doctor=doctor_ref)
        report_ids = [str(s["id"]) for s in report]
        assert str(initiated["id"]) in report_ids, "self-initiated sessions must appear in usage reports"

        init_row = next(s for s in report if str(s["id"]) == str(initiated["id"]))
        assert init_row["source"] == "self_initiated"
        assert init_row["doctor_id"] is None

    await _cleanup([patient.id, doctor.id], [scenario_a.id, scenario_b.id])
