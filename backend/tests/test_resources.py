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

async def _get_auth_headers(ac: AsyncClient, role: str) -> dict:
    email = f"{role}_{uuid.uuid4().hex[:6]}@campus.edu"
    if role == "admin":
        await _create_admin_user(email, "pass123")
    else:
        signup_payload = {
            "email": email,
            "password": "pass123",
            "role": role,
            "state": "Delhi",
            "city": "New Delhi"
        }
        await ac.post("/api/v1/auth/signup", json=signup_payload)

    login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": "pass123"})
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_resource_crud_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_headers = await _get_auth_headers(ac, "admin")
        patient_headers = await _get_auth_headers(ac, "patient")

        # 1. Admin creates a draft resource
        payload = {
            "title": "Coping with Exam Stress",
            "description": "A guide on managing study anxiety.",
            "resource_type": "pdf",
            "category": "academic",
            "author": "Dr. Smith",
            "is_published": False
        }
        res = await ac.post("/api/v1/resources", json=payload, headers=admin_headers)
        assert res.status_code == 201, res.text
        data = res.json()
        resource_id = data["id"]
        assert data["title"] == "Coping with Exam Stress"
        assert data["is_published"] is False

        # 2. Patient cannot see draft resource
        res = await ac.get(f"/api/v1/resources/{resource_id}", headers=patient_headers)
        assert res.status_code == 404

        # 3. Admin publishes the resource
        res = await ac.patch(f"/api/v1/resources/{resource_id}", json={"is_published": True}, headers=admin_headers)
        assert res.status_code == 200, res.text
        assert res.json()["is_published"] is True

        # 4. Patient can now see published resource
        res = await ac.get(f"/api/v1/resources/{resource_id}", headers=patient_headers)
        assert res.status_code == 200, res.text
        assert res.json()["title"] == "Coping with Exam Stress"

        # 5. Patient listing resources sees the published one
        res = await ac.get("/api/v1/resources", headers=patient_headers)
        assert res.status_code == 200, res.text
        items = res.json()
        assert any(r["id"] == resource_id for r in items)

        # 6. Admin deletes the resource
        res = await ac.delete(f"/api/v1/resources/{resource_id}", headers=admin_headers)
        assert res.status_code == 204

        # Verify deleted
        res = await ac.get(f"/api/v1/resources/{resource_id}", headers=admin_headers)
        assert res.status_code == 404
