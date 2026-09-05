import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.doctor import DoctorProfile


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _signup_and_login(ac: AsyncClient, role: str, **extra) -> tuple[str, str, str]:
    email = f"h2_{role}_{uuid.uuid4().hex[:6]}@test.com"
    password = "secret123"
    payload = {
        "email": email,
        "password": password,
        "role": role,
        "full_name": "Test User",
        "state": "Delhi",
        "city": "New Delhi",
    }
    payload.update(extra)
    res = await ac.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 200, res.text
    login = await ac.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"], email, password


async def _delete_user(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if not user:
            return
        profile = (
            await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
        ).scalars().first()
        if profile:
            await db.delete(profile)
        await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_patient_updates_own_profile_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token, email, _ = await _signup_and_login(ac, "patient")
        me = await ac.get("/api/v1/auth/me", headers=_auth(token))
        assert me.status_code == 200
        assert me.json()["phone"] is None
        assert me.json()["emergency_contact_phone"] is None

        body = {
            "full_name": "Updated Name",
            "phone": "9876543210",
            "emergency_contact_phone": "9123456789",
            "state": "Maharashtra",
            "city": "Pune",
        }
        res = await ac.put("/api/v1/auth/me", json=body, headers=_auth(token))
        assert res.status_code == 200, res.text
        updated = res.json()
        assert updated["full_name"] == "Updated Name"
        assert updated["phone"] == "9876543210"
        assert updated["emergency_contact_phone"] == "9123456789"
        assert updated["state"] == "Maharashtra"
        assert updated["city"] == "Pune"
        assert updated["email"] is not None
        assert updated["role"] == "patient"
        await _delete_user(email)


@pytest.mark.asyncio
async def test_doctor_updates_specialty_and_languages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token, email, _ = await _signup_and_login(
            ac,
            "doctor",
            license_number="MCI-2026-0002",
            specialty="Counselor / Therapist",
            languages=["English", "Hindi"],
        )
        me = await ac.get("/api/v1/auth/me", headers=_auth(token))
        assert me.status_code == 200
        assert me.json()["specialty"] == "Counselor / Therapist"
        assert me.json()["languages"] == ["English", "Hindi"]

        body = {
            "full_name": "Dr. Updated",
            "phone": "9811111111",
            "specialty": "Clinical Psychologist",
            "languages": ["English", "Hindi", "Marathi"],
        }
        res = await ac.put("/api/v1/auth/me", json=body, headers=_auth(token))
        assert res.status_code == 200, res.text
        updated = res.json()
        assert updated["full_name"] == "Dr. Updated"
        assert updated["phone"] == "9811111111"
        assert updated["specialty"] == "Clinical Psychologist"
        assert updated["languages"] == ["English", "Hindi", "Marathi"]
        await _delete_user(email)


@pytest.mark.asyncio
async def test_partial_update_keeps_other_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token, email, _ = await _signup_and_login(
            ac,
            "patient",
            full_name="Original Name",
            phone="9111111111",
            emergency_contact_phone="9222222222",
        )
        res = await ac.put(
            "/api/v1/auth/me",
            json={"city": "Mumbai"},
            headers=_auth(token),
        )
        assert res.status_code == 200, res.text
        updated = res.json()
        assert updated["city"] == "Mumbai"
        assert updated["state"] == "Delhi"
        assert updated["full_name"] == "Original Name"
        assert updated["phone"] == "9111111111"
        assert updated["emergency_contact_phone"] == "9222222222"
        await _delete_user(email)