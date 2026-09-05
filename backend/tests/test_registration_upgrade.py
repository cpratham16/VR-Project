import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User


@pytest.mark.asyncio
async def test_signup_persists_registration_profile_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "email": f"reg_g1_{uuid.uuid4().hex[:6]}@test.com",
            "password": "secret123",
            "role": "patient",
            "full_name": "Priya Sharma",
            "phone": "+919876543210",
            "emergency_contact_phone": "+919876543211",
            "state": "Maharashtra",
            "city": "Pune",
        }
        response = await ac.post("/api/v1/auth/signup", json=payload)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["full_name"] == "Priya Sharma"
        assert body["state"] == "Maharashtra"

    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == payload["email"]))
        ).scalars().first()
        assert user is not None
        assert user.full_name == "Priya Sharma"
        assert user.phone == "+919876543210"
        assert user.emergency_contact_phone == "+919876543211"

        await db.delete(user)
        await db.commit()
