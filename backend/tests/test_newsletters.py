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
async def test_newsletter_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_headers = await _get_headers(ac, "admin")
        patient_headers = await _get_headers(ac, "patient")

        # 1. Admin creates draft newsletter
        res = await ac.post("/api/v1/newsletters", json={
            "title": "September Campus Wellness Bulletin",
            "content": "Welcome back students! Here are stress management tips...",
            "summary": "Monthly wellness update",
            "author": "Wellness Center",
            "is_published": False
        }, headers=admin_headers)
        assert res.status_code == 201, res.text
        data = res.json()
        nl_id = data["id"]
        assert data["is_published"] is False

        # 2. Patient cannot view draft
        res = await ac.get(f"/api/v1/newsletters/{nl_id}", headers=patient_headers)
        assert res.status_code == 404

        # 3. Admin publishes newsletter
        res = await ac.patch(f"/api/v1/newsletters/{nl_id}", json={"is_published": True}, headers=admin_headers)
        assert res.status_code == 200, res.text
        assert res.json()["is_published"] is True
        assert res.json()["published_at"] is not None

        # 4. Patient views published newsletter
        res = await ac.get(f"/api/v1/newsletters/{nl_id}", headers=patient_headers)
        assert res.status_code == 200, res.text
        assert res.json()["title"] == "September Campus Wellness Bulletin"

        # 5. Patient lists newsletters
        res = await ac.get("/api/v1/newsletters", headers=patient_headers)
        assert res.status_code == 200, res.text
        items = res.json()
        assert any(n["id"] == nl_id for n in items)

        # 6. Admin deletes newsletter
        res = await ac.delete(f"/api/v1/newsletters/{nl_id}", headers=admin_headers)
        assert res.status_code == 204
