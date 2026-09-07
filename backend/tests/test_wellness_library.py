import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User

async def _create_admin_user(email: str, password: str = "pass123"):
    async with AsyncSessionLocal() as db:
        admin = User(
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_verified=True,
        )
        db.add(admin)
        await db.commit()

async def _get_headers(ac: AsyncClient, role: str) -> dict:
    email = f"{role}_{uuid.uuid4().hex[:6]}@campus.edu"
    if role == "admin":
        await _create_admin_user(email, "pass123")
    else:
        await ac.post("/api/v1/auth/signup", json={
            "email": email, "password": "pass123", "role": role, "state": "Delhi", "city": "New Delhi"
        })
    login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": "pass123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_wellness_library_student_progress():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_headers = await _get_headers(ac, "admin")
        patient_headers = await _get_headers(ac, "patient")

        # 1. Admin creates a published resource
        res = await ac.post("/api/v1/resources", json={
            "title": "Mindfulness & Sleep Guide",
            "description": "Techniques for better sleep and relaxation.",
            "resource_type": "pdf",
            "category": "sleep",
            "is_published": True
        }, headers=admin_headers)
        assert res.status_code == 201, res.text
        resource_id = res.json()["id"]

        # 2. Patient views library
        lib_res = await ac.get("/api/v1/resources/my-library", headers=patient_headers)
        assert lib_res.status_code == 200, lib_res.text
        items = lib_res.json()
        target = next((item for item in items if item["id"] == resource_id), None)
        assert target is not None
        assert target["progress"] is None

        # 3. Patient saves resource for later & updates progress to 50%
        prog_res = await ac.post(f"/api/v1/resources/{resource_id}/progress", json={
            "saved_for_later": True,
            "progress_percent": 50
        }, headers=patient_headers)
        assert prog_res.status_code == 200, prog_res.text
        assert prog_res.json()["saved_for_later"] is True
        assert prog_res.json()["progress_percent"] == 50
        assert prog_res.json()["is_completed"] is False

        # 4. Query my-library with saved_only=True filter
        saved_res = await ac.get("/api/v1/resources/my-library?saved_only=true", headers=patient_headers)
        assert saved_res.status_code == 200, saved_res.text
        saved_items = saved_res.json()
        assert any(item["id"] == resource_id for item in saved_items)

        # 5. Mark as completed (100%)
        comp_res = await ac.post(f"/api/v1/resources/{resource_id}/progress", json={
            "is_completed": True
        }, headers=patient_headers)
        assert comp_res.status_code == 200, comp_res.text
        assert comp_res.json()["is_completed"] is True
        assert comp_res.json()["progress_percent"] == 100
