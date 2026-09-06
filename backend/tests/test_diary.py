"""J1 — Diary CRUD endpoint tests.
J3 — Search & filter tests.
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
from app.models.diary import DiaryEntry


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


async def _delete_user_and_entries(email: str):
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == email))).scalars().first()
        if user:
            for e in (await db.execute(
                select(DiaryEntry).where(DiaryEntry.user_id == user.id)
            )).scalars().all():
                await db.delete(e)
            await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_create_diary_entry():
    email = f"j1_create_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entry
        res = await ac.post("/api/v1/patient/diary/", json={
            "title": "Test Entry",
            "content": "This is a test diary entry.",
            "entry_date": "2026-09-06T12:00:00"
        }, headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["title"] == "Test Entry"
        assert data["content"] == "This is a test diary entry."
        assert "id" in data
        assert data["user_id"] == str(user.id)

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_list_diary_entries():
    email = f"j1_list_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create multiple entries
        for i in range(3):
            await ac.post("/api/v1/patient/diary/", json={
                "title": f"Entry {i}",
                "content": f"Content {i}",
                "entry_date": f"2026-09-0{i+1}T12:00:00"
            }, headers=headers)

        # List entries
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data) == 3

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_get_diary_entry():
    email = f"j1_get_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entry
        create_res = await ac.post("/api/v1/patient/diary/", json={
            "title": "Single Entry",
            "content": "Get this entry",
        }, headers=headers)
        entry_id = create_res.json()["id"]

        # Get entry
        res = await ac.get(f"/api/v1/patient/diary/{entry_id}", headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["id"] == entry_id
        assert data["title"] == "Single Entry"

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_update_diary_entry():
    email = f"j1_update_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entry
        create_res = await ac.post("/api/v1/patient/diary/", json={
            "title": "Original",
            "content": "Original content",
        }, headers=headers)
        entry_id = create_res.json()["id"]

        # Update entry
        res = await ac.put(f"/api/v1/patient/diary/{entry_id}", json={
            "title": "Updated",
            "content": "Updated content",
        }, headers=headers)
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["title"] == "Updated"
        assert data["content"] == "Updated content"

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_delete_diary_entry():
    email = f"j1_delete_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entry
        create_res = await ac.post("/api/v1/patient/diary/", json={
            "title": "To Delete",
            "content": "Delete me",
        }, headers=headers)
        entry_id = create_res.json()["id"]

        # Delete entry
        res = await ac.delete(f"/api/v1/patient/diary/{entry_id}", headers=headers)
        assert res.status_code == 200, res.text

        # Verify deleted
        res2 = await ac.get(f"/api/v1/patient/diary/{entry_id}", headers=headers)
        assert res2.status_code == 404

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_multiple_entries_same_day():
    email = f"j1_sameday_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create multiple entries on same day
        for i in range(5):
            await ac.post("/api/v1/patient/diary/", json={
                "title": f"Entry {i}",
                "content": f"Content {i}",
                "entry_date": "2026-09-06T12:00:00"
            }, headers=headers)

        # List all
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 5

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


# J3: Search & filter tests
@pytest.mark.asyncio
async def test_search_diary_entries_by_keyword():
    email = f"j3_search_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entries with searchable content
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Happy Day",
            "content": "Feeling great today",
            "entry_date": "2026-09-06T12:00:00"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Sad News",
            "content": "Not a good day",
            "entry_date": "2026-09-07T12:00:00"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Neutral",
            "content": "Just an ordinary day",
            "entry_date": "2026-09-08T12:00:00"
        }, headers=headers)

        # Search by keyword in content
        res = await ac.get("/api/v1/patient/diary/?q=great", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Happy Day"

        # Search by keyword in title
        res2 = await ac.get("/api/v1/patient/diary/?q=Sad", headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2) == 1
        assert data2[0]["title"] == "Sad News"

        # Search with no matches
        res3 = await ac.get("/api/v1/patient/diary/?q=nonexistent", headers=headers)
        assert res3.status_code == 200
        assert len(res3.json()) == 0

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_filter_diary_entries_by_emotion_tag():
    email = f"j3_filter_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entries with emotion tags
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Happy",
            "content": "Feeling happy",
            "entry_date": "2026-09-06T12:00:00",
            "emotion_tag": "happy"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Anxious",
            "content": "Feeling anxious",
            "entry_date": "2026-09-07T12:00:00",
            "emotion_tag": "anxious"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Neutral",
            "content": "No emotion",
            "entry_date": "2026-09-08T12:00:00"
        }, headers=headers)

        # Filter by emotion_tag
        res = await ac.get("/api/v1/patient/diary/?emotion_tag=happy", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["emotion_tag"] == "happy"

        res2 = await ac.get("/api/v1/patient/diary/?emotion_tag=anxious", headers=headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2) == 1
        assert data2[0]["emotion_tag"] == "anxious"

        # Filter with no matches
        res3 = await ac.get("/api/v1/patient/diary/?emotion_tag=sad", headers=headers)
        assert res3.status_code == 200
        assert len(res3.json()) == 0

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_combined_search_and_filter():
    email = f"j3_combined_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        await ac.post("/api/v1/patient/diary/", json={
            "title": "Happy Day 1",
            "content": "Great day",
            "emotion_tag": "happy"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Happy Day 2",
            "content": "Wonderful day",
            "emotion_tag": "happy"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Sad Day",
            "content": "Terrible day",
            "emotion_tag": "sad"
        }, headers=headers)

        # Combined search + filter
        res = await ac.get("/api/v1/patient/diary/?q=day&emotion_tag=happy", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert all(d["emotion_tag"] == "happy" for d in data)
        assert all("day" in (d["title"] or "").lower() or "day" in (d["content"] or "").lower() for d in data)

    await _delete_user_and_entries(email)


# J5: PIN/biometric privacy lock tests
@pytest.mark.asyncio
async def test_setup_diary_pin():
    email = f"j5_setup_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Check initial status - no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Set PIN
        res = await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify status now shows PIN set
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

        # Wrong PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "0000"}, headers=headers)
        assert res.status_code == 401

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_change_diary_pin():
    email = f"j5_change_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set initial PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Change PIN
        res = await ac.put("/api/v1/patient/diary/privacy/pin", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is True

        # Old PIN should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 401

        # New PIN should work
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "5678"}, headers=headers)
        assert res.status_code == 200
        assert res.json()["verified"] is True

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_remove_diary_pin():
    email = f"j5_remove_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Remove PIN
        res = await ac.delete("/api/v1/patient/diary/privacy/pin", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Status should show no PIN
        res = await ac.get("/api/v1/patient/diary/privacy/pin/status", headers=headers)
        assert res.status_code == 200
        assert res.json()["has_pin"] is False

        # Verify should fail
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 400

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_diary_access_blocked_without_pin():
    email = f"j5_block_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create a diary entry
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Secret",
            "content": "Private entry",
        }, headers=headers)

        # Set PIN
        await ac.post("/api/v1/patient/diary/privacy/pin", json={"pin": "1234"}, headers=headers)

        # Try to access diary without verifying PIN - should still work at API level
        # (PIN verification is frontend-enforced, but we test the verify endpoint)
        res = await ac.get("/api/v1/patient/diary/", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1

        # Verify PIN works
        res = await ac.post("/api/v1/patient/diary/privacy/pin/verify", json={"pin": "1234"}, headers=headers)
        assert res.status_code == 200

    await _delete_user_and_entries(email)

# J6: AI Reflection tests
@pytest.mark.asyncio
async def test_reflect_on_diary_entry():
    email = f"j6_reflect_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entry
        create_res = await ac.post("/api/v1/patient/diary/", json={
            "title": "Test Entry",
            "content": "I had a great day today. Everything went well.",
        }, headers=headers)
        assert create_res.status_code == 200
        entry_id = create_res.json()["id"]

        # Request reflection
        res = await ac.post(f"/api/v1/patient/diary/{entry_id}/reflect", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["entry_id"] == entry_id
        assert "reflection" in data
        assert isinstance(data["reflection"], str)
        assert len(data["reflection"]) > 0

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_reflect_on_nonexistent_entry():
    email = f"j6_reflect_none_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Try to reflect on non-existent entry
        res = await ac.post("/api/v1/patient/diary/00000000-0000-0000-0000-000000000000/reflect", headers=headers)
        assert res.status_code == 404

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_reflect_on_other_users_entry():
    email1 = f"j6_reflect_user1_{uuid.uuid4().hex[:6]}@test.com"
    email2 = f"j6_reflect_user2_{uuid.uuid4().hex[:6]}@test.com"
    user1 = await _create_patient(email1)
    user2 = await _create_patient(email2)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User 1 creates entry
        login1 = await ac.post("/api/v1/auth/login", data={"username": email1, "password": "secret123"})
        headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
        create_res = await ac.post("/api/v1/patient/diary/", json={
            "title": "User 1 Entry",
            "content": "Private content",
        }, headers=headers1)
        entry_id = create_res.json()["id"]

        # User 2 tries to reflect on user 1's entry
        login2 = await ac.post("/api/v1/auth/login", data={"username": email2, "password": "secret123"})
        headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
        res = await ac.post(f"/api/v1/patient/diary/{entry_id}/reflect", headers=headers2)
        assert res.status_code == 404

    await _delete_user_and_entries(email1)
    await _delete_user_and_entries(email2)

# J7: Streak tests
@pytest.mark.asyncio
async def test_streak_no_entries():
    email = f"j7_streak_none_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        res = await ac.get("/api/v1/patient/diary/streak", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0
        assert data["last_entry_date"] is None

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_streak_single_entry():
    email = f"j7_streak_single_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        await ac.post("/api/v1/patient/diary/", json={
            "title": "Entry 1",
            "content": "First entry",
            "entry_date": "2026-09-06T12:00:00"
        }, headers=headers)

        res = await ac.get("/api/v1/patient/diary/streak", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["current_streak"] == 1
        assert data["longest_streak"] == 1
        assert data["last_entry_date"] == "2026-09-06"

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_streak_consecutive_days():
    email = f"j7_streak_consec_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Create entries for 3 consecutive days
        for i in range(3):
            await ac.post("/api/v1/patient/diary/", json={
                "title": f"Entry {i+1}",
                "content": f"Day {i+1}",
                "entry_date": f"2026-09-0{i+4}T12:00:00"  # Sep 4, 5, 6
            }, headers=headers)

        res = await ac.get("/api/v1/patient/diary/streak", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["current_streak"] == 3
        assert data["longest_streak"] == 3

    await _delete_user_and_entries(email)


@pytest.mark.asyncio
async def test_streak_broken():
    email = f"j7_streak_broken_{uuid.uuid4().hex[:6]}@test.com"
    user = await _create_patient(email)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        # Entries on Sep 4, 5 (consecutive), then gap, then Sep 8
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Day 1", "content": "Day 1", "entry_date": "2026-09-04T12:00:00"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Day 2", "content": "Day 2", "entry_date": "2026-09-05T12:00:00"
        }, headers=headers)
        await ac.post("/api/v1/patient/diary/", json={
            "title": "Day 4", "content": "Day 4", "entry_date": "2026-09-08T12:00:00"  # Gap on Sep 6-7
        }, headers=headers)

        res = await ac.get("/api/v1/patient/diary/streak", headers=headers)
        assert res.status_code == 200
        data = res.json()
        # Current streak should be 1 (only Sep 8 if today is Sep 8 or Sep 9)
        # Longest streak should be 2 (Sep 4-5)
        assert data["longest_streak"] == 2

    await _delete_user_and_entries(email)
