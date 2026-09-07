import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.notification import NotificationRecord
from app.services.email_service import deliver_campaign_email

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
async def test_email_delivery_service_helper():
    # Test delivery helper without SMTP returns simulated status
    status, err = deliver_campaign_email("test@campus.edu", "Test Subject", "<p>Hello</p>")
    assert status == "sent"
    assert err is None

@pytest.mark.asyncio
async def test_publishing_triggers_in_app_notifications():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_headers = await _get_headers(ac, "admin")

        # 1. Publishing a resource generates an in-app notification record
        res = await ac.post("/api/v1/resources", json={
            "title": "Coping Strategies Vol 1",
            "description": "Resource test",
            "resource_type": "pdf",
            "category": "coping",
            "is_published": True
        }, headers=admin_headers)
        assert res.status_code == 201, res.text

        async with AsyncSessionLocal() as db:
            notifs = (await db.execute(
                select(NotificationRecord).where(
                    NotificationRecord.recipient_type == "resource_announcement",
                    NotificationRecord.content_preview.like("%Coping Strategies Vol 1%")
                )
            )).scalars().all()
            assert len(notifs) >= 1

        # 2. Publishing a newsletter generates an in-app notification record
        nl_res = await ac.post("/api/v1/newsletters", json={
            "title": "Weekly Health Alert",
            "content": "Stay healthy!",
            "is_published": True
        }, headers=admin_headers)
        assert nl_res.status_code == 201, nl_res.text

        async with AsyncSessionLocal() as db:
            notifs = (await db.execute(
                select(NotificationRecord).where(
                    NotificationRecord.recipient_type == "newsletter_announcement",
                    NotificationRecord.content_preview.like("%Weekly Health Alert%")
                )
            )).scalars().all()
            assert len(notifs) >= 1
