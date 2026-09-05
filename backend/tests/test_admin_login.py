import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.anonymized import RegionalAggregate
from app.api.v1.admin import get_overview, get_trend


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _login(ac: AsyncClient, email: str, password: str):
    return await ac.post("/api/v1/auth/login", data={"username": email, "password": password})


async def _create_db_admin(email: str, password: str = "secret123"):
    async with AsyncSessionLocal() as db:
        admin = User(
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin


async def _delete_users(emails: list[str]):
    async with AsyncSessionLocal() as db:
        for email in emails:
            user = (await db.execute(select(User).where(User.email == email))).scalars().first()
            if user:
                await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_signup_rejects_admin_role():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/auth/signup", json={
            "email": f"h5_admin_{uuid.uuid4().hex[:6]}@test.com",
            "password": "secret123",
            "role": "admin",
        })
        assert res.status_code == 400, res.text
        assert "Admin accounts must be created" in res.json()["detail"]


@pytest.mark.asyncio
async def test_admin_create_endpoint_and_login_roundtrip():
    boss_email = f"h5_boss_{uuid.uuid4().hex[:6]}@test.com"
    new_email = f"h5_new_{uuid.uuid4().hex[:6]}@test.com"
    await _create_db_admin(boss_email)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await _login(ac, boss_email, "secret123")
        assert login.status_code == 200, login.text
        boss_token = login.json()["access_token"]

        created = await ac.post(
            "/api/v1/admin/users",
            headers=_auth(boss_token),
            json={
                "email": new_email,
                "password": "admin_pass_1",
                "full_name": "New Admin",
                "state": "Karnataka",
                "city": "Bengaluru",
            },
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["role"] == "admin"
        assert body["is_verified"] is True

        new_login = await _login(ac, new_email, "admin_pass_1")
        assert new_login.status_code == 200, new_login.text
        me = await ac.get("/api/v1/auth/me", headers=_auth(new_login.json()["access_token"]))
        assert me.status_code == 200
        assert me.json()["role"] == "admin"

        dup = await ac.post(
            "/api/v1/admin/users",
            headers=_auth(boss_token),
            json={"email": new_email, "password": "whatever123"},
        )
        assert dup.status_code == 400, dup.text

    await _delete_users([boss_email, new_email])


@pytest.mark.asyncio
async def test_non_admin_cannot_create_admin():
    patient_email = f"h5_pt_{uuid.uuid4().hex[:6]}@test.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        signup = await ac.post("/api/v1/auth/signup", json={
            "email": patient_email,
            "password": "secret123",
            "role": "patient",
            "state": "Maharashtra",
            "city": "Pune",
        })
        assert signup.status_code == 200, signup.text
        login = await _login(ac, patient_email, "secret123")
        assert login.status_code == 200, login.text

        res = await ac.post(
            "/api/v1/admin/users",
            headers=_auth(login.json()["access_token"]),
            json={"email": f"h5_x_{uuid.uuid4().hex[:6]}@test.com", "password": "secret123"},
        )
        assert res.status_code == 403, res.text

    await _delete_users([patient_email])


@pytest.mark.asyncio
async def test_state_admin_jurisdiction_matches_city_state_regions():
    """A state-scoped admin must see rows keyed as '{city}, {state}', not only bare '{state}'."""
    admin_email = f"h5_ka_{uuid.uuid4().hex[:6]}@test.com"
    state = f"H5State{uuid.uuid4().hex[:4]}"
    city = f"H5City{uuid.uuid4().hex[:4]}"
    region = f"{city}, {state}"

    async with AsyncSessionLocal() as db:
        admin = User(
            email=admin_email,
            hashed_password=get_password_hash("secret123"),
            role="admin",
            state=state,
            is_verified=True,
        )
        db.add(admin)
        await db.flush()
        agg = RegionalAggregate(
            region=region,
            period="2026-08",
            total_patients=15,
            screening_count=15,
            phq9_mild=8,
            phq9_moderate=7,
            risk_alert_count=2,
        )
        db.add(agg)
        await db.commit()
        await db.refresh(admin)

        overview = await get_overview(db=db, current_admin=admin)
        assert overview["suppressed"] is False
        assert overview["total_patients"] == 15
        assert overview["regions_covered"] == 1

        trend = await get_trend(region=region, db=db, current_admin=admin)
        assert len(trend) == 1
        assert trend[0]["region"] == region
        assert trend[0]["suppressed"] is False

        t_global = await get_trend(region=None, db=db, current_admin=admin)
        assert [r["region"] for r in t_global] == [region]

        with pytest.raises(Exception) as exc_info:
            await get_trend(region="Some Other State", db=db, current_admin=admin)
        assert exc_info.value.status_code == 403

        await db.delete(agg)
        await db.delete(admin)
        await db.commit()