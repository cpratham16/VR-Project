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

async def _get_headers_and_email(ac: AsyncClient, role: str) -> tuple[dict, str]:
    email = f"{role}_{uuid.uuid4().hex[:6]}@campus.edu"
    if role == "admin":
        await _create_admin_user(email, "pass123")
    else:
        await ac.post("/api/v1/auth/signup", json={
            "email": email, "password": "pass123", "role": role, "state": "Delhi", "city": "New Delhi"
        })
    login_res = await ac.post("/api/v1/auth/login", data={"username": email, "password": "pass123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, email

@pytest.mark.asyncio
async def test_campaign_creation_and_sending_with_privacy_safeguards():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_headers, admin_email = await _get_headers_and_email(ac, "admin")
        student_headers, student_email = await _get_headers_and_email(ac, "patient")

        # 1. Test N8 Privacy validation safeguard: invalid clinical audience_type rejected
        res = await ac.post("/api/v1/campaigns", json={
            "title": "Invalid Campaign",
            "subject": "Test",
            "body_html": "<p>Content</p>",
            "audience_type": "phq9_severe_patients"
        }, headers=admin_headers)
        assert res.status_code == 422  # Pydantic validation error

        # 2. Student sets opt-out preference (unsubscribe from non-essential communications)
        unsub_res = await ac.post("/api/v1/patient/unsubscribe", json={"unsubscribed": True}, headers=student_headers)
        assert unsub_res.status_code == 200
        assert unsub_res.json()["unsubscribed"] is True

        # 3. Admin creates valid non-clinical campaign targeting students
        res = await ac.post("/api/v1/campaigns", json={
            "title": "Exam Prep Announcement",
            "subject": "Quiet Study Spaces Open",
            "body_html": "<p>Library extended hours starting today.</p>",
            "audience_type": "students"
        }, headers=admin_headers)
        assert res.status_code == 201, res.text
        campaign_id = res.json()["id"]

        # 4. Admin sends campaign
        send_res = await ac.post(f"/api/v1/campaigns/{campaign_id}/send", headers=admin_headers)
        assert send_res.status_code == 200, send_res.text
        data = send_res.json()
        assert data["status"] == "sent"

        # The unsubscribed student must be excluded from recipient list
        recipients_emails = [r["email"] for r in data["recipients"]]
        assert student_email not in recipients_emails
