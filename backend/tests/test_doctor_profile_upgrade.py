import os
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User
from app.models.doctor import DoctorProfile


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _signup_and_login(ac: AsyncClient, role: str, **extra) -> tuple[str, str]:
    email = f"g2_{role}_{uuid.uuid4().hex[:6]}@test.com"
    password = "secret123"
    if role == "admin":
        async with AsyncSessionLocal() as db:
            db.add(User(
                email=email,
                hashed_password=get_password_hash(password),
                role="admin",
                full_name="Test Admin",
                is_verified=True,
            ))
            await db.commit()
    else:
        payload = {
            "email": email,
            "password": password,
            "role": role,
            "full_name": "Test Doc",
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
    return login.json()["access_token"], email


async def _delete_user_and_cascade(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if not user:
            return None
        profile = (
            await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
        ).scalars().first()
        path = profile.credential_path if profile else None
        if profile:
            await db.delete(profile)
        await db.delete(user)
        await db.commit()
        if path and os.path.exists(path):
            os.remove(path)
        return path


@pytest.mark.asyncio
async def test_doctor_signup_creates_profile_without_credentials():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token, email = await _signup_and_login(
            ac,
            "doctor",
            license_number="MCI-2026-0001",
            specialty="Counselor / Therapist",
            languages=["English", "Hindi"],
        )
        me = await ac.get("/api/v1/auth/me", headers=_auth(token))
        assert me.status_code == 200
        body = me.json()
        assert body["role"] == "doctor"
        assert body["has_credentials"] is False

        status_res = await ac.get("/api/v1/doctor/profile", headers=_auth(token))
        assert status_res.status_code == 200
        assert status_res.json()["has_credentials"] is False

    await _delete_user_and_cascade(email)


@pytest.mark.asyncio
async def test_credential_upload_roundtrip_and_admin_download():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        doc_token, doc_email = await _signup_and_login(
            ac, "doctor", license_number="MCI-2026-0002", languages=["English"]
        )
        admin_token, admin_email = await _signup_and_login(ac, "admin")

        files = {"file": ("license.pdf", b"%PDF-1.4 fake-license-content", "application/pdf")}
        up = await ac.post(
            "/api/v1/doctor/profile/credential",
            headers=_auth(doc_token),
            files=files,
        )
        assert up.status_code == 200, up.text
        stored_path = up.json()["credential_filename"]

        me = await ac.get("/api/v1/auth/me", headers=_auth(doc_token))
        assert me.json()["has_credentials"] is True

        dl = await ac.get("/api/v1/admin/doctors/nonexistent-id/credential", headers=_auth(admin_token))
        assert dl.status_code == 404

        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User).where(User.email == doc_email))).scalars().first()
            real_id = str(user.id)

        dl_ok = await ac.get(
            f"/api/v1/admin/doctors/{real_id}/credential", headers=_auth(admin_token)
        )
        assert dl_ok.status_code == 200
        assert dl_ok.content.startswith(b"%PDF")

        forbidden = await ac.get(
            f"/api/v1/admin/doctors/{real_id}/credential", headers=_auth(doc_token)
        )
        assert forbidden.status_code in (401, 403)

        upload_dir = settings.CREDENTIAL_UPLOAD_DIR
        matches = [f for f in os.listdir(upload_dir) if f.endswith(".pdf")]
        assert any(stored_path.endswith(".pdf") for _ in matches)

        await _delete_user_and_cascade(doc_email)
        await _delete_user_and_cascade(admin_email)


@pytest.mark.asyncio
async def test_credential_upload_rejects_bad_type_and_oversize():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        doc_token, doc_email = await _signup_and_login(
            ac, "doctor", license_number="MCI-2026-0003", languages=["English"]
        )

        bad_type = await ac.post(
            "/api/v1/doctor/profile/credential",
            headers=_auth(doc_token),
            files={"file": ("malware.exe", b"MZ...", "application/x-msdownload")},
        )
        assert bad_type.status_code == 400

        oversize = await ac.post(
            "/api/v1/doctor/profile/credential",
            headers=_auth(doc_token),
            files={"file": ("big.pdf", b"x" * (settings.CREDENTIAL_MAX_SIZE_MB * 1024 * 1024 + 1), "application/pdf")},
        )
        assert oversize.status_code == 400

        missing_license = await ac.post(
            "/api/v1/auth/signup",
            json={
                "email": f"g2_nolicense_{uuid.uuid4().hex[:6]}@test.com",
                "password": "secret123",
                "role": "doctor",
                "languages": ["English"],
            },
        )
        assert missing_license.status_code == 400
        assert "license" in missing_license.json()["detail"].lower()

        await _delete_user_and_cascade(doc_email)
