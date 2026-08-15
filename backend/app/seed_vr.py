"""Seed the two default VR exposure scenarios if they are not present."""
import asyncio
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.vr import VRScenario

DEFAULT_SCENARIOS = [
    {
        "slug": "heights",
        "name": "Skyline Terrace",
        "phobia_type": "acrophobia",
        "description": "A glass observation deck high above a low-poly city. Progressive exposure to looking over the railing and approaching the edge, with guided breathing prompts.",
        "is_active": True,
    },
    {
        "slug": "public_speaking",
        "name": "Lecture Hall",
        "phobia_type": "glossophobia",
        "description": "A university auditorium with a podium and audience avatars. Progressive exposure to greeting the audience, delivering lines, maintaining eye contact, and taking questions.",
        "is_active": True,
    },
]

async def seed():
    async with AsyncSessionLocal() as db:
        for data in DEFAULT_SCENARIOS:
            existing = await db.execute(
                select(VRScenario).where(VRScenario.slug == data["slug"])
            )
            if existing.scalars().first() is None:
                db.add(VRScenario(**data))
        await db.commit()
        print("VR scenarios seeded.")

if __name__ == "__main__":
    asyncio.run(seed())
