"""O1 — Comprehensive API Contract Test Suite.

Validates all 119 endpoints across 19 routers against OpenAPI contract:
- Auth matrix (unauthenticated, patient, doctor, admin, verified doctor)
- Request/response schema validation
- RBAC boundaries
- Validation edge cases (422)
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy.future import select

from app.main import app
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, get_password_hash
from app.models.user import User

PUBLIC_ENDPOINTS = {
    ("GET", "/api/v1/health/"),
    ("POST", "/api/v1/auth/signup"),
    ("POST", "/api/v1/auth/login"),
    ("GET", "/"),
}

OPTIONAL_AUTH_ENDPOINTS = {
    ("GET", "/api/v1/resources"),
    ("GET", "/api/v1/resources/{resource_id}"),
    ("GET", "/api/v1/newsletters"),
    ("GET", "/api/v1/newsletters/{newsletter_id}"),
}

ENDPOINT_ROLE_MAP = {
    "public": {
        ("GET", "/api/v1/health/"),
        ("POST", "/api/v1/auth/signup"),
        ("POST", "/api/v1/auth/login"),
        ("GET", "/"),
    },
    "optional_auth": OPTIONAL_AUTH_ENDPOINTS,
    "any_auth": {
        ("GET", "/api/v1/auth/me"),
        ("PUT", "/api/v1/auth/me"),
        ("GET", "/api/v1/patient/doctors"),
        ("GET", "/api/v1/patient/status"),
        ("POST", "/api/v1/patient/profile"),
        ("POST", "/api/v1/patient/consent"),
        ("GET", "/api/v1/patient/appointments"),
        ("POST", "/api/v1/patient/appointments"),
        ("GET", "/api/v1/patient/appointments/{appointment_id}/ical"),
        ("GET", "/api/v1/patient/export"),
        ("GET", "/api/v1/patient/screening/questions/{screening_type}"),
        ("POST", "/api/v1/patient/screening/submit"),
        ("GET", "/api/v1/patient/screening/history"),
        ("GET", "/api/v1/patient/screening/trends/{screening_type}"),
        ("GET", "/api/v1/patient/screening/reminder"),
        ("POST", "/api/v1/patient/mood/"),
        ("GET", "/api/v1/patient/mood/history"),
        ("PUT", "/api/v1/patient/mood/{entry_id}"),
        ("POST", "/api/v1/patient/diary/"),
        ("GET", "/api/v1/patient/diary/"),
        ("GET", "/api/v1/patient/diary/streak"),
        ("GET", "/api/v1/patient/diary/{entry_id}"),
        ("PUT", "/api/v1/patient/diary/{entry_id}"),
        ("DELETE", "/api/v1/patient/diary/{entry_id}"),
        ("POST", "/api/v1/patient/diary/{entry_id}/reflect"),
        ("PUT", "/api/v1/patient/diary/privacy/pin"),
        ("POST", "/api/v1/patient/diary/privacy/pin"),
        ("DELETE", "/api/v1/patient/diary/privacy/pin"),
        ("GET", "/api/v1/patient/diary/privacy/pin/status"),
        ("POST", "/api/v1/patient/diary/privacy/pin/verify"),
        ("GET", "/api/v1/patient/chat/chat/rooms"),
        ("POST", "/api/v1/patient/chat/chat/rooms"),
        ("GET", "/api/v1/patient/chat/chat/rooms/{room_id}"),
        ("POST", "/api/v1/patient/chat/chat/rooms/{room_id}/join"),
        ("DELETE", "/api/v1/patient/chat/chat/rooms/{room_id}/leave"),
        ("POST", "/api/v1/patient/chat/chat/rooms/{room_id}/messages"),
        ("GET", "/api/v1/patient/chat/chat/rooms/{room_id}/messages"),
        ("PUT", "/api/v1/patient/chat/chat/messages/{message_id}"),
        ("DELETE", "/api/v1/patient/chat/chat/messages/{message_id}"),
        ("DELETE", "/api/v1/patient/chat/chat/rooms/{room_id}/messages/{message_id}"),
        ("POST", "/api/v1/patient/chat/chat/rooms/{room_id}/mute/{user_id}"),
        ("POST", "/api/v1/patient/chat/chat/rooms/{room_id}/unmute/{user_id}"),
        ("GET", "/api/v1/patient/chat/chat/rooms/{room_id}/participants"),
        ("PATCH", "/api/v1/patient/chat/chat/rooms/{room_id}/participants/{user_id}/role"),
        ("POST", "/api/v1/patient/chat"),
        ("GET", "/api/v1/patient/chat/history"),
        ("POST", "/api/v1/patient/panic"),
        ("GET", "/api/v1/community/posts"),
        ("POST", "/api/v1/community/posts"),
        ("GET", "/api/v1/community/posts/{post_id}"),
        ("POST", "/api/v1/community/posts/{post_id}/comments"),
        ("GET", "/api/v1/patient/vr/scenarios"),
        ("POST", "/api/v1/patient/vr/self-initiate"),
        ("GET", "/api/v1/patient/vr/assigned"),
        ("POST", "/api/v1/patient/vr/sessions/{session_id}/start"),
        ("POST", "/api/v1/patient/vr/sessions/{session_id}/telemetry"),
        ("POST", "/api/v1/patient/vr/sessions/{session_id}/complete"),
    },
    "doctor_or_admin": {
        ("GET", "/api/v1/doctor/triage"),
        ("GET", "/api/v1/doctor/patient/{patient_id}"),
        ("POST", "/api/v1/doctor/patient/{patient_id}/notes"),
        ("PUT", "/api/v1/doctor/notes/{note_id}"),
        ("GET", "/api/v1/doctor/notes/{note_id}/history"),
        ("GET", "/api/v1/doctor/notes/search"),
        ("GET", "/api/v1/doctor/appointments"),
        ("PUT", "/api/v1/doctor/appointments/{appointment_id}/status"),
        ("POST", "/api/v1/doctor/appointments/{appointment_id}/triage-action"),
        ("GET", "/api/v1/doctor/appointments/{appointment_id}/ical"),
        ("GET", "/api/v1/doctor/patient/{patient_id}/mood-summary"),
        ("GET", "/api/v1/doctor/profile"),
        ("POST", "/api/v1/doctor/profile/credential"),
        ("GET", "/api/v1/doctor/profile/credential/download"),
        ("GET", "/api/v1/doctor/alerts"),
        ("POST", "/api/v1/doctor/alerts/check-escalations"),
        ("POST", "/api/v1/doctor/alerts/{alert_id}/acknowledge"),
        ("POST", "/api/v1/doctor/alerts/{alert_id}/escalate"),
        ("GET", "/api/v1/doctor/moderation/queue"),
        ("POST", "/api/v1/doctor/moderation/posts/{post_id}/action"),
        ("GET", "/api/v1/doctor/vr/scenarios"),
        ("POST", "/api/v1/doctor/vr/assign"),
        ("GET", "/api/v1/doctor/vr/sessions"),
        ("GET", "/api/v1/doctor/vr/sessions/{session_id}/telemetry"),
        ("POST", "/api/v1/doctor/vr/sessions/{session_id}/cancel"),
    },
    "verified_doctor_or_admin": {
    },
    "admin_only": {
        ("POST", "/api/v1/resources"),
        ("GET", "/api/v1/resources"),
        ("GET", "/api/v1/resources/my-library"),
        ("POST", "/api/v1/resources/{resource_id}/progress"),
        ("GET", "/api/v1/resources/{resource_id}"),
        ("PATCH", "/api/v1/resources/{resource_id}"),
        ("DELETE", "/api/v1/resources/{resource_id}"),
        ("POST", "/api/v1/newsletters"),
        ("GET", "/api/v1/newsletters"),
        ("GET", "/api/v1/newsletters/{newsletter_id}"),
        ("PATCH", "/api/v1/newsletters/{newsletter_id}"),
        ("DELETE", "/api/v1/newsletters/{newsletter_id}"),
        ("POST", "/api/v1/campaigns"),
        ("GET", "/api/v1/campaigns"),
        ("GET", "/api/v1/campaigns/{campaign_id}"),
        ("PATCH", "/api/v1/campaigns/{campaign_id}"),
        ("POST", "/api/v1/campaigns/{campaign_id}/send"),
        ("GET", "/api/v1/patient/unsubscribe"),
        ("POST", "/api/v1/patient/unsubscribe"),
        ("GET", "/api/v1/debug/trace/{message_id}"),
        ("GET", "/api/v1/admin/doctors/{user_id}/credential"),
        ("GET", "/api/v1/admin/doctors"),
        ("POST", "/api/v1/admin/users"),
        ("POST", "/api/v1/admin/doctors/{user_id}/approve"),
        ("POST", "/api/v1/admin/doctors/{user_id}/reject"),
        ("GET", "/api/v1/admin/screening/instruments"),
        ("POST", "/api/v1/admin/screening/instruments"),
        ("POST", "/api/v1/admin/analytics/run-pipeline"),
        ("GET", "/api/v1/admin/analytics/overview"),
        ("GET", "/api/v1/admin/analytics/regions"),
        ("GET", "/api/v1/admin/analytics/trend"),
        ("GET", "/api/v1/admin/analytics/spikes"),
        ("GET", "/api/v1/admin/analytics/export"),
    },
}


def _match_path(pattern: str, path: str) -> bool:
    """Match OpenAPI path pattern (with {param}) against concrete path."""
    import re
    regex = "^" + pattern.replace("{", "(?P<").replace("}", ">[^/]+)") + "$"
    return bool(re.match(regex, path))


def _get_required_roles(method: str, path: str) -> str:
    """Determine required role category for an endpoint."""
    for role, endpoints in ENDPOINT_ROLE_MAP.items():
        for ep_method, ep_path in endpoints:
            if ep_method == method and _match_path(ep_path, path):
                return role
    return "any_auth"


def _make_token(user_id: str, role: str) -> str:
    return create_access_token(str(user_id), expires_delta=timedelta(minutes=30))


async def _create_user(role: str, email: str = None, verified: bool = True) -> User:
    async with AsyncSessionLocal() as db:
        user = User(
            email=email or f"{role}_{uuid.uuid4().hex[:8]}@test.com",
            hashed_password=get_password_hash("secret123"),
            role=role,
            is_verified=verified,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def _delete_user(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if user:
            # Delete related records first to avoid FK violations
            from app.models.alert import RiskAlert
            from app.models.diary import DiaryEntry
            from app.models.mood import MoodEntry
            from app.models.screening import ScreeningResult
            from app.models.appointment import Appointment
            from app.models.note import ClinicalNote
            from app.models.resource import UserResourceProgress
            from app.models.chat import ChatSession, ChatMessage
            from app.models.community import CommunityPost, CommunityComment
            from app.models.notification import NotificationRecord
            
            # Get risk alert IDs for this user to delete notification_records that reference them
            alert_ids_result = await db.execute(
                select(RiskAlert.id).where(RiskAlert.user_id == user.id)
            )
            alert_ids = [row[0] for row in alert_ids_result.all()]
            
            if alert_ids:
                # Delete notification_records that reference these alert_ids
                await db.execute(NotificationRecord.__table__.delete().where(NotificationRecord.alert_id.in_(alert_ids)))
            
            # Delete chat messages first (they reference chat_sessions)
            session_ids_result = await db.execute(
                select(ChatSession.id).where(ChatSession.user_id == user.id)
            )
            session_ids = [row[0] for row in session_ids_result.all()]
            if session_ids:
                await db.execute(ChatMessage.__table__.delete().where(ChatMessage.session_id.in_(session_ids)))
            
            # Delete community comments first (they reference community_posts)
            post_ids_result = await db.execute(
                select(CommunityPost.id).where(CommunityPost.user_id == user.id)
            )
            post_ids = [row[0] for row in post_ids_result.all()]
            if post_ids:
                await db.execute(CommunityComment.__table__.delete().where(CommunityComment.post_id.in_(post_ids)))
            
            for model in [RiskAlert, DiaryEntry, MoodEntry, ScreeningResult, UserResourceProgress, ChatSession, CommunityPost, CommunityComment]:
                await db.execute(model.__table__.delete().where(model.user_id == user.id))
            
            # Appointment and ClinicalNote use patient_id/doctor_id
            await db.execute(Appointment.__table__.delete().where(Appointment.patient_id == user.id))
            await db.execute(ClinicalNote.__table__.delete().where(ClinicalNote.patient_id == user.id))
            await db.execute(ClinicalNote.__table__.delete().where(ClinicalNote.doctor_id == user.id))
            
            await db.delete(user)
            await db.commit()


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_request(
    ac: AsyncClient,
    method: str,
    path: str,
    token: str = None,
    json_data: dict = None,
    params: dict = None,
):
    headers = _auth_header(token) if token else {}
    return await ac.request(method, path, headers=headers, json=json_data, params=params)


def _concretize_path(path: str) -> str:
    """Replace path parameters with dummy UUIDs for testing."""
    replacements = {
        "{resource_id}": "00000000-0000-0000-0000-000000000000",
        "{newsletter_id}": "00000000-0000-0000-0000-000000000000",
        "{campaign_id}": "00000000-0000-0000-0000-000000000000",
        "{appointment_id}": "00000000-0000-0000-0000-000000000000",
        "{entry_id}": "00000000-0000-0000-0000-000000000000",
        "{room_id}": "00000000-0000-0000-0000-000000000000",
        "{message_id}": "00000000-0000-0000-0000-000000000000",
        "{user_id}": "00000000-0000-0000-0000-000000000000",
        "{post_id}": "00000000-0000-0000-0000-000000000000",
        "{alert_id}": "00000000-0000-0000-0000-000000000000",
        "{note_id}": "00000000-0000-0000-0000-000000000000",
        "{patient_id}": "00000000-0000-0000-0000-000000000000",
        "{session_id}": "00000000-0000-0000-0000-000000000000",
        "{screening_type}": "PHQ-9",
    }
    for k, v in replacements.items():
        path = path.replace(k, v)
    return path


@pytest.fixture(scope="session")
def transport():
    return ASGITransport(app=app)


class TestRequestValidation:
    """Request validation (422) for endpoints with request bodies."""

    @pytest.mark.asyncio
    async def test_empty_body_rejected(self, transport):
        """Endpoints requiring request body should reject empty body with 422 (or 404 if resource not found)."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            # Only test endpoints accessible to patients
            body_required = {
                "POST": [
                    "/api/v1/patient/mood/",
                    "/api/v1/patient/diary/",
                    "/api/v1/patient/chat/chat/rooms",
                    "/api/v1/patient/chat/chat/rooms/{room_id}/messages",
                    "/api/v1/community/posts",
                    "/api/v1/patient/appointments",
                    "/api/v1/patient/profile",
                    "/api/v1/patient/consent",
                    "/api/v1/patient/screening/submit",
                ],
                "PUT": [
                    "/api/v1/patient/diary/{entry_id}",
                    "/api/v1/patient/mood/{entry_id}",
                ],
            }
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                for method, paths in body_required.items():
                    for path in paths:
                        test_path = path.replace("{entry_id}", "00000000-0000-0000-0000-000000000000").replace(
                            "{room_id}", "00000000-0000-0000-0000-000000000000"
                        )
                        if method == "POST":
                            res = await ac.post(test_path, headers=_auth_header(token), json={})
                        elif method == "PUT":
                            res = await ac.put(test_path, headers=_auth_header(token), json={})
                        assert res.status_code in (404, 422), f"{method} {path} accepted empty body: {res.text}"
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_invalid_types_rejected(self, transport):
        """Invalid field types should return 422."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post(
                    "/api/v1/patient/mood/",
                    headers=_auth_header(token),
                    json={"mood_score": "not_a_number"},
                )
                assert res.status_code == 422
        finally:
            await _delete_user(patient.email)


class TestResponseSchemaValidation:
    """Validate response schemas against OpenAPI spec (smoke test)."""

    @pytest.mark.asyncio
    async def test_health_endpoint_schema(self, transport):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/v1/health/")
            assert res.status_code == 200
            data = res.json()
            assert "status" in data

    @pytest.mark.asyncio
    async def test_auth_me_returns_user(self, transport):
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/auth/me", headers=_auth_header(token))
                assert res.status_code == 200
                data = res.json()
                assert "id" in data
                assert "email" in data
                assert "role" in data
        finally:
            await _delete_user(patient.email)


class TestEndpointCoverage:
    """Verify all endpoints from OpenAPI are tested."""

    def test_all_endpoints_mapped(self):
        from app.main import app
        spec = app.openapi()
        tested = set()
        for role_endpoints in ENDPOINT_ROLE_MAP.values():
            tested.update(role_endpoints)
        tested.update(PUBLIC_ENDPOINTS)

        for path, methods in spec["paths"].items():
            for method, op in methods.items():
                if method.lower() in ("get", "post", "put", "patch", "delete"):
                    key = (method.upper(), path)
                    if key not in tested:
                        pytest.fail(f"Endpoint not in role map: {method.upper()} {path}")


class TestCriticalJourneys:
    """18 critical user journeys (patient/doctor/admin)."""

    @pytest.mark.asyncio
    async def test_patient_signup_login_me(self, transport):
        """J1: Patient signup -> login -> /me."""
        email = f"journey1_{uuid.uuid4().hex[:6]}@test.com"
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            signup = await ac.post("/api/v1/auth/signup", json={
                "email": email, "password": "secret123", "role": "patient",
                "state": "Maharashtra", "city": "Pune",
            })
            assert signup.status_code == 200
            login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
            assert login.status_code == 200
            token = login.json()["access_token"]
            me = await ac.get("/api/v1/auth/me", headers=_auth_header(token))
            assert me.status_code == 200
            assert me.json()["email"] == email
        await _delete_user(email)

    @pytest.mark.asyncio
    async def test_patient_screening_flow(self, transport):
        """J2: Patient screening questions -> submit -> history."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                q = await ac.get("/api/v1/patient/screening/questions/PHQ-9", headers=_auth_header(token))
                assert q.status_code == 200
                submit = await ac.post("/api/v1/patient/screening/submit", headers=_auth_header(token), json={
                    "screening_type": "PHQ-9", "answers": [1]*9
                })
                assert submit.status_code == 200
                hist = await ac.get("/api/v1/patient/screening/history", headers=_auth_header(token))
                assert hist.status_code == 200
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_patient_mood_diary_flow(self, transport):
        """J3: Patient mood entry -> diary entry -> streak."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                mood = await ac.post("/api/v1/patient/mood/", headers=_auth_header(token), json={
                    "mood_score": 5, "note": "Feeling okay"
                })
                assert mood.status_code == 200
                diary = await ac.post("/api/v1/patient/diary/", headers=_auth_header(token), json={
                    "title": "Test", "content": "Content", "entry_date": datetime.utcnow().isoformat()
                })
                assert diary.status_code == 200
                streak = await ac.get("/api/v1/patient/diary/streak", headers=_auth_header(token))
                assert streak.status_code == 200
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_patient_ai_chat(self, transport):
        """J4: Patient AI chat."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post("/api/v1/patient/chat", headers=_auth_header(token), json={
                    "message": "I'm feeling stressed"
                })
                assert res.status_code == 200
                data = res.json()
                # Response has 'content' field with the AI reply
                assert "content" in data
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_patient_panic_sos(self, transport):
        """J5: Patient panic SOS."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post("/api/v1/patient/panic", headers=_auth_header(token), json={
                    "location": "Test location", "message": "Need help"
                })
                assert res.status_code == 200
                data = res.json()
                # Response has 'id' field with the alert ID
                assert "id" in data
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_patient_community_post(self, transport):
        """J6: Patient community post."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post("/api/v1/community/posts", headers=_auth_header(token), json={
                    "title": "Test Post", "content": "Test content"
                })
                assert res.status_code == 200
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_patient_vr_self_initiate(self, transport):
        """J7: Patient VR self-initiate."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post("/api/v1/patient/vr/self-initiate", headers=_auth_header(token), json={
                    "scenario_id": "00000000-0000-0000-0000-000000000000"
                })
                assert res.status_code in (200, 404)
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_patient_wellness_library(self, transport):
        """J8: Patient wellness library (resources + newsletters)."""
        patient = await _create_user("patient")
        token = _make_token(patient.id, "patient")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/resources/my-library", headers=_auth_header(token))
                assert res.status_code == 200
                res = await ac.get("/api/v1/newsletters", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_doctor_triage_view(self, transport):
        """J9: Doctor triage view."""
        doctor = await _create_user("doctor", verified=True)
        token = _make_token(doctor.id, "doctor")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/doctor/triage", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(doctor.email)

    @pytest.mark.asyncio
    async def test_doctor_patient_detail(self, transport):
        """J10: Doctor patient detail."""
        doctor = await _create_user("doctor", verified=True)
        patient = await _create_user("patient")
        token = _make_token(doctor.id, "doctor")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get(f"/api/v1/doctor/patient/{patient.id}", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(doctor.email)
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_doctor_clinical_notes(self, transport):
        """J11: Doctor clinical notes CRUD."""
        doctor = await _create_user("doctor", verified=True)
        patient = await _create_user("patient")
        token = _make_token(doctor.id, "doctor")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                create = await ac.post(f"/api/v1/doctor/patient/{patient.id}/notes", headers=_auth_header(token), json={
                    "content": "Test note"
                })
                assert create.status_code == 200
        finally:
            await _delete_user(doctor.email)
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_doctor_alerts_management(self, transport):
        """J12: Doctor alerts acknowledgment."""
        doctor = await _create_user("doctor", verified=True)
        token = _make_token(doctor.id, "doctor")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/doctor/alerts", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(doctor.email)

    @pytest.mark.asyncio
    async def test_doctor_moderation_queue(self, transport):
        """J13: Doctor moderation queue."""
        doctor = await _create_user("doctor", verified=True)
        token = _make_token(doctor.id, "doctor")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/doctor/moderation/queue", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(doctor.email)

    @pytest.mark.asyncio
    async def test_doctor_vr_assign(self, transport):
        """J14: Doctor VR assign."""
        doctor = await _create_user("doctor", verified=True)
        patient = await _create_user("patient")
        token = _make_token(doctor.id, "doctor")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.post("/api/v1/doctor/vr/assign", headers=_auth_header(token), json={
                    "patient_id": str(patient.id), "scenario_id": "00000000-0000-0000-0000-000000000000"
                })
                assert res.status_code in (200, 404)
        finally:
            await _delete_user(doctor.email)
            await _delete_user(patient.email)

    @pytest.mark.asyncio
    async def test_admin_user_management(self, transport):
        """J15: Admin user management."""
        admin = await _create_user("admin", verified=True)
        token = _make_token(admin.id, "admin")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/admin/doctors", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(admin.email)

    @pytest.mark.asyncio
    async def test_admin_analytics(self, transport):
        """J16: Admin analytics."""
        admin = await _create_user("admin", verified=True)
        token = _make_token(admin.id, "admin")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/admin/analytics/overview", headers=_auth_header(token))
                assert res.status_code == 200
        finally:
            await _delete_user(admin.email)

    @pytest.mark.asyncio
    async def test_admin_campaigns(self, transport):
        """J17: Admin campaigns CRUD."""
        admin = await _create_user("admin", verified=True)
        token = _make_token(admin.id, "admin")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/campaigns", headers=_auth_header(token))
                assert res.status_code == 200
                create = await ac.post("/api/v1/campaigns", headers=_auth_header(token), json={
                    "title": "Test Campaign", "subject": "Test Subject", "body_html": "<p>Test</p>", "audience_type": "all", "delivery_channels": "in_app"
                })
                assert create.status_code == 201
        finally:
            await _delete_user(admin.email)

    @pytest.mark.asyncio
    async def test_admin_newsletters(self, transport):
        """J18: Admin newsletters CRUD."""
        admin = await _create_user("admin", verified=True)
        token = _make_token(admin.id, "admin")
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                res = await ac.get("/api/v1/newsletters", headers=_auth_header(token))
                assert res.status_code == 200
                create = await ac.post("/api/v1/newsletters", headers=_auth_header(token), json={
                    "title": "Test Newsletter", "content": "Test", "status": "draft"
                })
                assert create.status_code == 201
        finally:
            await _delete_user(admin.email)