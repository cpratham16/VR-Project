import os
import uuid
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.appointment import Appointment


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _signup(ac: AsyncClient, role: str, state=None, city=None) -> tuple[str, str]:
    email = f"g4_{role}_{uuid.uuid4().hex[:6]}@test.com"
    if role == "admin":
        async with AsyncSessionLocal() as db:
            db.add(User(
                email=email,
                hashed_password=get_password_hash("secret123"),
                role="admin",
                state=state,
                city=city,
                is_verified=True,
            ))
            await db.commit()
    else:
        payload = {"email": email, "password": "secret123", "role": role}
        if role == "patient":
            payload.update({"state": state, "city": city})
        else:
            payload.update({
                "state": state,
                "city": city,
                "license_number": f"LIC-{uuid.uuid4().hex[:8].upper()}",
                "languages": ["English"],
            })
        res = await ac.post("/api/v1/auth/signup", json=payload)
        assert res.status_code == 200, res.text
    login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
    return login.json()["access_token"], email


async def _upload_credential(ac: AsyncClient, token: str):
    res = await ac.post(
        "/api/v1/doctor/profile/credential",
        headers=_auth(token),
        files={"file": ("license.pdf", b"%PDF-1.4 test-license", "application/pdf")},
    )
    assert res.status_code == 200, res.text


async def _cleanup(emails):
    async with AsyncSessionLocal() as db:
        for email in emails:
            user = (await db.execute(select(User).where(User.email == email))).scalars().first()
            if not user:
                continue
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
                if profile.credential_path and os.path.exists(profile.credential_path):
                    try:
                        os.remove(profile.credential_path)
                    except OSError:
                        pass
                await db.delete(profile)
            await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_pending_doctor_blocked_then_approved():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _signup(ac, "patient", "Gujarat", "Ahmedabad")
        doc_token, doc_email = await _signup(ac, "doctor", "Gujarat", "Ahmedabad")
        admin_token, admin_email = await _signup(ac, "admin")

        me = await ac.get("/api/v1/auth/me", headers=_auth(doc_token))
        assert me.json()["review_status"] == "pending"
        assert me.json()["is_verified"] is False

        triage = await ac.get("/api/v1/doctor/triage", headers=_auth(doc_token))
        assert triage.status_code == 403
        assert "DOCTOR_PENDING_REVIEW" in triage.json()["detail"]

        appts = await ac.get("/api/v1/doctor/appointments", headers=_auth(doc_token))
        assert appts.status_code == 403

        self_verify = await ac.post("/api/v1/doctor/verify-self", headers=_auth(doc_token))
        assert self_verify.status_code == 403

        directory = await ac.get("/api/v1/patient/doctors", headers=_auth(pat_token))
        async with AsyncSessionLocal() as db:
            doc_id = str((await db.execute(select(User).where(User.email == doc_email))).scalars().first().id)
        assert doc_id not in [d["id"] for d in directory.json()["doctors"]]

        queue = await ac.get("/api/v1/admin/doctors?status=pending", headers=_auth(admin_token))
        queue_ids = [d["user_id"] for d in queue.json()]
        assert doc_id in queue_ids

        await _upload_credential(ac, doc_token)
        approve = await ac.post(f"/api/v1/admin/doctors/{doc_id}/approve", json={}, headers=_auth(admin_token))
        assert approve.status_code == 200, approve.text

        me2 = await ac.get("/api/v1/auth/me", headers=_auth(doc_token))
        assert me2.json()["review_status"] == "approved"
        assert me2.json()["is_verified"] is True

        triage2 = await ac.get("/api/v1/doctor/triage", headers=_auth(doc_token))
        assert triage2.status_code == 200

        directory2 = await ac.get("/api/v1/patient/doctors", headers=_auth(pat_token))
        assert doc_id in [d["id"] for d in directory2.json()["doctors"]]

        await _cleanup([pat_email, doc_email, admin_email])


@pytest.mark.asyncio
async def test_rejection_reason_visible_and_resubmission_resets_to_pending():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        pat_token, pat_email = await _signup(ac, "patient", "Rajasthan", "Jaipur")
        doc_token, doc_email = await _signup(ac, "doctor", "Rajasthan", "Jaipur")
        admin_token, admin_email = await _signup(ac, "admin")

        await _upload_credential(ac, doc_token)

        async with AsyncSessionLocal() as db:
            doc_id = str((await db.execute(select(User).where(User.email == doc_email))).scalars().first().id)

        reject = await ac.post(
            f"/api/v1/admin/doctors/{doc_id}/reject",
            json={},
            headers=_auth(admin_token),
        )
        assert reject.status_code == 400

        reject_ok = await ac.post(
            f"/api/v1/admin/doctors/{doc_id}/reject",
            json={"reason": "License number could not be verified"},
            headers=_auth(admin_token),
        )
        assert reject_ok.status_code == 200

        profile = await ac.get("/api/v1/doctor/profile", headers=_auth(doc_token))
        body = profile.json()
        assert body["review_status"] == "rejected"
        assert body["rejection_reason"] == "License number could not be verified"

        me = await ac.get("/api/v1/auth/me", headers=_auth(doc_token))
        assert me.json()["rejection_reason"] == "License number could not be verified"

        directory = await ac.get("/api/v1/patient/doctors", headers=_auth(pat_token))
        assert doc_id not in [d["id"] for d in directory.json()["doctors"]]

        reup = await ac.post(
            "/api/v1/doctor/profile/credential",
            headers=_auth(doc_token),
            files={"file": ("fixed-license.pdf", b"%PDF-1.4 corrected", "application/pdf")},
        )
        assert reup.status_code == 200
        assert reup.json()["review_status"] == "pending"

        profile2 = await ac.get("/api/v1/doctor/profile", headers=_auth(doc_token))
        assert profile2.json()["review_status"] == "pending"
        assert profile2.json()["rejection_reason"] is None

        await _cleanup([pat_email, doc_email, admin_email])


@pytest.mark.asyncio
async def test_doctor_appointments_scoped_to_own_and_unassigned():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        doc_a_token, doc_a_email = await _signup(ac, "doctor", "Delhi", "New Delhi")
        doc_b_token, doc_b_email = await _signup(ac, "doctor", "Delhi", "New Delhi")
        pat_token, pat_email = await _signup(ac, "patient", "Delhi", "New Delhi")

        for token in [doc_a_token, doc_b_token]:
            await _upload_credential(ac, token)
        async with AsyncSessionLocal() as db:
            a_id = (await db.execute(select(User).where(User.email == doc_a_email))).scalars().first()
            b_id = (await db.execute(select(User).where(User.email == doc_b_email))).scalars().first()
            p_id = (await db.execute(select(User).where(User.email == pat_email))).scalars().first()
            a_id.is_verified = True
            b_id.is_verified = True
            await db.commit()
            a_uuid, b_uuid, p_uuid = a_id.id, b_id.id, p_id.id

        future = datetime.utcnow() + timedelta(days=2)
        own = Appointment(patient_id=p_uuid, doctor_id=a_uuid, scheduled_at=future, status="confirmed")
        other = Appointment(patient_id=p_uuid, doctor_id=b_uuid, scheduled_at=future, status="requested")
        unassigned = Appointment(patient_id=p_uuid, doctor_id=None, scheduled_at=future, status="requested")
        async with AsyncSessionLocal() as db:
            db.add_all([own, other, unassigned])
            await db.commit()

        res = await ac.get("/api/v1/doctor/appointments", headers=_auth(doc_a_token))
        assert res.status_code == 200
        ids = [a["id"] for a in res.json()]
        async with AsyncSessionLocal() as db:
            own_id = str(own.id)
            other_id = str(other.id)
            unassigned_id = str(unassigned.id)

        assert own_id in ids, "doctor must see their own appointments"
        assert unassigned_id in ids, "unassigned requests must remain visible"
        assert other_id not in ids, "another doctor's appointments must be hidden"

        claim_attempt = await ac.put(
            f"/api/v1/doctor/appointments/{other_id}/status",
            json={"status": "confirmed"},
            headers=_auth(doc_a_token),
        )
        assert claim_attempt.status_code == 403

        await _cleanup([pat_email, doc_a_email, doc_b_email])
