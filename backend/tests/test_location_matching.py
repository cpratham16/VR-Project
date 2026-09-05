import uuid
from datetime import datetime
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.doctor import DoctorProfile


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _make_user(ac: AsyncClient, role: str, state: str = None, city: str = None, **extra) -> tuple[str, str]:
    email = f"g3_{role}_{uuid.uuid4().hex[:6]}@test.com"
    password = "secret123"
    payload = {"email": email, "password": password, "role": role}
    if role == "patient":
        payload.update({"state": state, "city": city})
    else:
        payload.update({
            "state": state,
            "city": city,
            "license_number": extra.get("license_number", f"LIC-{uuid.uuid4().hex[:8].upper()}"),
            "languages": extra.get("languages", ["English"]),
        })
        if "specialty" in extra:
            payload["specialty"] = extra["specialty"]
    res = await ac.post("/api/v1/auth/signup", json=payload)
    assert res.status_code == 200, res.text
    login = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"], email


async def _set_verified(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        user.is_verified = True
        profile = (
            await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
        ).scalars().first()
        if profile and not profile.credential_filename:
            profile.credential_filename = "test-credential.pdf"
            profile.uploaded_at = datetime.utcnow()
        await db.commit()


async def _delete_user(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if user:
            from app.models.appointment import Appointment
            appts = (
                await db.execute(
                    select(Appointment).where(
                        (Appointment.patient_id == user.id) | (Appointment.doctor_id == user.id)
                    )
                )
            ).scalars().all()
            for a in appts:
                await db.delete(a)
            profile = (
                await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
            ).scalars().first()
            if profile:
                await db.delete(profile)
            await db.delete(user)
            await db.commit()


@pytest.mark.asyncio
async def test_location_ranking_and_broaden():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _make_user(ac, "patient", state="Maharashtra", city="Pune")

        local_doc, local_email = await _make_user(ac, "doctor", state="Maharashtra", city="Pune")
        state_doc, state_email = await _make_user(ac, "doctor", state="Maharashtra", city="Nagpur")
        far_doc, far_email = await _make_user(ac, "doctor", state="Kerala", city="Kochi")

        await _set_verified(local_email)
        await _set_verified(state_email)
        await _set_verified(far_email)

        res_default = await ac.get("/api/v1/patient/doctors", headers=_auth(pat_token))
        assert res_default.status_code == 200
        data_default = res_default.json()
        ids_default = [d["id"] for d in data_default["doctors"]]
        assert data_default["broadened"] is False
        assert data_default["patient_location"]["state"] == "Maharashtra"
        assert len(ids_default) >= 2

        async with AsyncSessionLocal() as db:
            lid = str((await db.execute(select(User).where(User.email == local_email))).scalars().first().id)
            sid = str((await db.execute(select(User).where(User.email == state_email))).scalars().first().id)
            fid = str((await db.execute(select(User).where(User.email == far_email))).scalars().first().id)

        assert lid in ids_default and sid in ids_default
        assert fid not in ids_default, "out-of-region doctor must be hidden without broaden"
        assert ids_default.index(lid) < ids_default.index(sid), "same-city doctor must rank first"

        res_broad = await ac.get("/api/v1/patient/doctors?broaden=true", headers=_auth(pat_token))
        assert res_broad.status_code == 200
        data_broad = res_broad.json()
        ids_broad = [d["id"] for d in data_broad["doctors"]]
        assert data_broad["broadened"] is True
        assert fid in ids_broad, "broadened search must reveal out-of-region doctors"
        assert ids_broad.index(lid) < ids_broad.index(fid)

        for email in [pat_email, local_email, state_email, far_email]:
            await _delete_user(email)


@pytest.mark.asyncio
async def test_unverified_and_uncredentialed_doctors_excluded():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _make_user(ac, "patient", state="Delhi", city="New Delhi")

        unverified_doc, unv_email = await _make_user(ac, "doctor", state="Delhi", city="New Delhi")

        verified_nocred, nc_email = await _make_user(ac, "doctor", state="Delhi", city="New Delhi")
        await _set_verified(nc_email)
        async with AsyncSessionLocal() as db:
            u = (await db.execute(select(User).where(User.email == nc_email))).scalars().first()
            p = (await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == u.id))).scalars().first()
            p.credential_filename = None
            await db.commit()

        res = await ac.get("/api/v1/patient/doctors", headers=_auth(pat_token))
        ids = [d["id"] for d in res.json()["doctors"]]
        async with AsyncSessionLocal() as db:
            unv_id = str((await db.execute(select(User).where(User.email == unv_email))).scalars().first().id)
            nc_id = str((await db.execute(select(User).where(User.email == nc_email))).scalars().first().id)

        assert unv_id not in ids, "unverified doctor must never appear"
        assert nc_id not in ids, "doctor without credential file must never appear"

        for email in [pat_email, unv_email, nc_email]:
            await _delete_user(email)


@pytest.mark.asyncio
async def test_appointment_doctor_validation():
    from datetime import datetime, timedelta

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _make_user(ac, "patient", state="Maharashtra", city="Pune")

        future = (datetime.utcnow() + timedelta(days=3)).isoformat()

        bad_uuid = await ac.post(
            "/api/v1/patient/appointments",
            json={"scheduled_at": future, "doctor_id": str(uuid.uuid4())},
            headers=_auth(pat_token),
        )
        assert bad_uuid.status_code == 400

        patient_as_doctor, other_pat_email = await _make_user(ac, "patient", state="Maharashtra", city="Pune")
        async with AsyncSessionLocal() as db:
            other_id = str((await db.execute(select(User).where(User.email == other_pat_email))).scalars().first().id)
        wrong_role = await ac.post(
            "/api/v1/patient/appointments",
            json={"scheduled_at": future, "doctor_id": other_id},
            headers=_auth(pat_token),
        )
        assert wrong_role.status_code == 400

        doc_token, doc_email = await _make_user(ac, "doctor", state="Maharashtra", city="Pune")
        await _set_verified(doc_email)
        async with AsyncSessionLocal() as db:
            good_id = str((await db.execute(select(User).where(User.email == doc_email))).scalars().first().id)

        ok = await ac.post(
            "/api/v1/patient/appointments",
            json={"scheduled_at": future, "doctor_id": good_id, "reason": "G3 validation test"},
            headers=_auth(pat_token),
        )
        assert ok.status_code == 200, ok.text
        body = ok.json()
        assert body["doctor_id"] is not None
        assert body["doctor_state"] == "Maharashtra"

        listing = await ac.get("/api/v1/patient/appointments", headers=_auth(pat_token))
        match = next(a for a in listing.json() if a["id"] == body["id"])
        assert match["doctor_name"] is not None or match["doctor_city"] is not None

        for email in [pat_email, other_pat_email, doc_email]:
            await _delete_user(email)
