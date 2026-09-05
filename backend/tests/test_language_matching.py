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


async def _make_user(ac: AsyncClient, role: str, state=None, city=None, languages=None) -> tuple[str, str]:
    email = f"g5_{role}_{uuid.uuid4().hex[:6]}@test.com"
    payload = {"email": email, "password": "secret123", "role": role}
    if role == "patient":
        payload.update({"state": state, "city": city})
    else:
        payload.update({
            "state": state,
            "city": city,
            "license_number": f"LIC-{uuid.uuid4().hex[:8].upper()}",
            "languages": languages or ["English"],
        })
    res = await ac.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 200, res.text
    login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
    return login.json()["access_token"], email


async def _approve(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        user.is_verified = True
        profile = (
            await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
        ).scalars().first()
        if profile:
            profile.credential_filename = "test-credential.pdf"
        await db.commit()


async def _delete_user(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if user:
            profile = (
                await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
            ).scalars().first()
            if profile:
                await db.delete(profile)
            await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_language_filter_single_select():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _make_user(ac, "patient", "Karnataka", "Bengaluru")

        hindi_doc, hindi_email = await _make_user(ac, "doctor", "Karnataka", "Bengaluru", ["English", "Hindi"])
        tamil_doc, tamil_email = await _make_user(ac, "doctor", "Karnataka", "Mysuru", ["English", "Tamil"])

        await _approve(hindi_email)
        await _approve(tamil_email)

        async with AsyncSessionLocal() as db:
            hindi_id = str((await db.execute(select(User).where(User.email == hindi_email))).scalars().first().id)
            tamil_id = str((await db.execute(select(User).where(User.email == tamil_email))).scalars().first().id)

        res_tamil = await ac.get(
            "/api/v1/patient/doctors?language=Tamil", headers=_auth(pat_token)
        )
        assert res_tamil.status_code == 200
        data_tamil = res_tamil.json()
        assert data_tamil["language_filter"] == "Tamil"
        ids_tamil = [d["id"] for d in data_tamil["doctors"]]
        assert tamil_id in ids_tamil
        assert hindi_id not in ids_tamil

        for doc in data_tamil["doctors"]:
            assert any(l.lower() == "tamil" for l in doc["languages"])

        res_lower = await ac.get(
            "/api/v1/patient/doctors?language=tamil", headers=_auth(pat_token)
        )
        assert tamil_id in [d["id"] for d in res_lower.json()["doctors"]]

        res_none = await ac.get(
            "/api/v1/patient/doctors?language=French", headers=_auth(pat_token)
        )
        assert res_none.status_code == 200
        assert res_none.json()["doctors"] == []

        res_all = await ac.get("/api/v1/patient/doctors", headers=_auth(pat_token))
        ids_all = [d["id"] for d in res_all.json()["doctors"]]
        assert hindi_id in ids_all and tamil_id in ids_all

        for email in [pat_email, hindi_email, tamil_email]:
            await _delete_user(email)


@pytest.mark.asyncio
async def test_language_filter_composes_with_broaden():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _make_user(ac, "patient", "Punjab", "Ludhiana")

        local_hindi, lh_email = await _make_user(ac, "doctor", "Punjab", "Ludhiana", ["English", "Hindi"])
        far_hindi, fh_email = await _make_user(ac, "doctor", "West Bengal", "Kolkata", ["Bengali", "Hindi"])
        far_tamil, ft_email = await _make_user(ac, "doctor", "Tamil Nadu", "Chennai", ["English", "Tamil"])

        for e in [lh_email, fh_email, ft_email]:
            await _approve(e)

        async with AsyncSessionLocal() as db:
            lh_id = str((await db.execute(select(User).where(User.email == lh_email))).scalars().first().id)
            fh_id = str((await db.execute(select(User).where(User.email == fh_email))).scalars().first().id)
            ft_id = str((await db.execute(select(User).where(User.email == ft_email))).scalars().first().id)

        scoped = await ac.get(
            "/api/v1/patient/doctors?language=Hindi", headers=_auth(pat_token)
        )
        ids_scoped = [d["id"] for d in scoped.json()["doctors"]]
        assert lh_id in ids_scoped
        assert fh_id not in ids_scoped and ft_id not in ids_scoped

        broadened = await ac.get(
            "/api/v1/patient/doctors?broaden=true&language=hindi", headers=_auth(pat_token)
        )
        ids_broad = [d["id"] for d in broadened.json()["doctors"]]
        assert lh_id in ids_broad
        assert fh_id in ids_broad
        assert ft_id not in ids_broad
        assert ids_broad.index(lh_id) < ids_broad.index(fh_id)

        for email in [pat_email, lh_email, fh_email, ft_email]:
            await _delete_user(email)
