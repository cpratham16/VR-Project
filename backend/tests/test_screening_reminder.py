"""I1 — per-instrument screening reminder endpoint tests.

Acceptance: GET /patient/screening/reminder keyed per instrument, so completing
one (e.g. PHQ-9) never suppresses the other (GAD-7).
"""
import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.screening import ScreeningResult


async def _create_patient(email: str):
    async with AsyncSessionLocal() as db:
        user = User(
            email=email,
            hashed_password=get_password_hash("secret123"),
            role="patient",
            state="Maharashtra",
            city="Pune",
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


async def _add_result(user_id, screening_type: str, score: int, band: str, days_ago: int):
    async with AsyncSessionLocal() as db:
        db.add(ScreeningResult(
            user_id=user_id,
            screening_type=screening_type,
            answers=[0] * (9 if screening_type == "PHQ-9" else 7),
            total_score=score,
            severity_band=band,
            created_at=datetime.utcnow() - timedelta(days=days_ago),
        ))
        await db.commit()


async def _delete_users(emails: list[str]):
    async with AsyncSessionLocal() as db:
        for email in emails:
            user = (await db.execute(select(User).where(User.email == email))).scalars().first()
            if user:
                for r in (await db.execute(
                    select(ScreeningResult).where(ScreeningResult.user_id == user.id)
                )).scalars().all():
                    await db.delete(r)
                await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_reminder_returns_both_instruments():
    email = f"i1_both_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        res = await ac.get("/api/v1/patient/screening/reminder", headers=headers)
        assert res.status_code == 200, res.text
        body = res.json()
        assert set(body.keys()) == {"PHQ-9", "GAD-7"}
        assert body["PHQ-9"]["should_remind"] is True
        assert body["PHQ-9"]["reason"] == "no_screening_on_record"
        assert body["GAD-7"]["should_remind"] is True

    await _delete_users([email])


@pytest.mark.asyncio
async def test_completed_phq9_does_not_suppress_gad7():
    email = f"i1_indep_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    await _add_result(user.id, "PHQ-9", 2, "Minimal", days_ago=2)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        res = await ac.get("/api/v1/patient/screening/reminder", headers=headers)
        assert res.status_code == 200, res.text
        body = res.json()
        # PHQ-9 done recently -> not due; GAD-7 untouched -> still reminds.
        assert body["PHQ-9"]["should_remind"] is False
        assert body["PHQ-9"]["reason"] == "not_due"
        assert body["GAD-7"]["should_remind"] is True
        assert body["GAD-7"]["reason"] == "no_screening_on_record"

    await _delete_users([email])