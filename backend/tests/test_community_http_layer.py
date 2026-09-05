import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.community import CommunityPost, CommunityComment


async def _signup_and_login(ac: AsyncClient, tag: str) -> tuple[str, str]:
    email = f"thr_{tag}_{uuid.uuid4().hex[:6]}@test.com"
    res = await ac.post("/api/v1/auth/signup", json={
        "email": email, "password": "secret123", "role": "patient",
        "state": "Delhi", "city": "New Delhi",
    })
    assert res.status_code == 200, res.text

    login = await ac.post("/api/v1/auth/login", data={"username": email, "password": "secret123"})
    token = login.json()["access_token"]
    prof = await ac.post(
        "/api/v1/patient/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"pseudonym": f"Thread_{tag}_{uuid.uuid4().hex[:4]}"},
    )
    assert prof.status_code == 200, prof.text
    return token, email


async def _cleanup(emails):
    async with AsyncSessionLocal() as db:
        for email in emails:
            user = (await db.execute(select(User).where(User.email == email))).scalars().first()
            if not user:
                continue
            posts = (await db.execute(select(CommunityPost).where(CommunityPost.user_id == user.id))).scalars().all()
            for post in posts:
                comments = (
                    await db.execute(select(CommunityComment).where(CommunityComment.post_id == post.id))
                ).scalars().all()
                for c in comments:
                    await db.delete(c)
                await db.delete(post)
            profile = (
                await db.execute(select(PatientProfile).where(PatientProfile.user_id == user.id))
            ).scalars().first()
            if profile:
                await db.delete(profile)
            await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_community_http_layer_threaded_replies_serialize():
    """HTTP-layer regression: GET /community/posts must serialize threaded replies
    without response_model validation errors (the D1-era 500 regression)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_a, email_a = await _signup_and_login(ac, "a")
        token_b, email_b = await _signup_and_login(ac, "b")
        auth_a = {"Authorization": f"Bearer {token_a}"}
        auth_b = {"Authorization": f"Bearer {token_b}"}

        created = await ac.post(
            "/api/v1/community/posts",
            headers=auth_a,
            json={"title": "Threaded regression post", "category": "Peer Support", "content": "Testing nested replies over HTTP."},
        )
        assert created.status_code == 200, created.text
        post_id = created.json()["id"]

        top = await ac.post(
            f"/api/v1/community/posts/{post_id}/comments",
            headers=auth_b,
            json={"content": "Top-level comment"},
        )
        assert top.status_code == 200, top.text
        top_id = str(top.json()["id"])

        reply = await ac.post(
            f"/api/v1/community/posts/{post_id}/comments",
            headers=auth_a,
            json={"content": "Nested reply", "parent_id": top_id},
        )
        assert reply.status_code == 200, reply.text
        assert str(reply.json()["parent_id"]) == top_id

        detail = await ac.get(f"/api/v1/community/posts/{post_id}", headers=auth_a)
        assert detail.status_code == 200, detail.text
        body = detail.json()
        assert body["comment_count"] == 2
        parent_map = {c["content"]: c["parent_id"] for c in body["comments"]}
        assert parent_map["Top-level comment"] is None
        assert parent_map["Nested reply"] is not None

        feed = await ac.get("/api/v1/community/posts", headers=auth_a)
        assert feed.status_code == 200, feed.text
        feed_post = next(p for p in feed.json() if p["id"] == post_id)
        assert feed_post["comment_count"] == 2

        await _cleanup([email_a, email_b])
