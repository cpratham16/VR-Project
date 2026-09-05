"""Seed screening instruments (PHQ-9, GAD-7) into the DB-backed engine.

Idempotent: upserts by `code`. Run AFTER `alembic upgrade head`:

    python -m app.seed_screening

Bands mirror the legacy hardcoded calculators exactly so behavior is unchanged.
"""
import asyncio

from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.screening_instrument import ScreeningInstrument

PHQ9 = {
    "code": "PHQ-9",
    "title": "PHQ-9 (Patient Health Questionnaire-9)",
    "instructions": "Over the last 2 weeks, how often have you been bothered by any of the following problems?",
    "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
    "questions": [
        {"id": 1, "text": "Little interest or pleasure in doing things"},
        {"id": 2, "text": "Feeling down, depressed, or hopeless"},
        {"id": 3, "text": "Trouble falling or staying asleep, or sleeping too much"},
        {"id": 4, "text": "Feeling tired or having little energy"},
        {"id": 5, "text": "Poor appetite or overeating"},
        {"id": 6, "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down"},
        {"id": 7, "text": "Trouble concentrating on things, such as reading the newspaper or watching television"},
        {"id": 8, "text": "Moving or speaking so slowly that other people could have noticed? Or being fidgety/restless"},
        {"id": 9, "text": "Thoughts that you would be better off dead, or of hurting yourself in some way"},
    ],
    "scoring_bands": [
        {"max_score": 4, "label": "Minimal"},
        {"max_score": 9, "label": "Mild"},
        {"max_score": 14, "label": "Moderate"},
        {"max_score": 19, "label": "Moderately Severe"},
        {"max_score": 27, "label": "Severe"},
    ],
    "answer_min": 0,
    "answer_max": 3,
    "critical_items": [9],
}

GAD7 = {
    "code": "GAD-7",
    "title": "GAD-7 (Generalized Anxiety Disorder-7)",
    "instructions": "Over the last 2 weeks, how often have you been bothered by the following problems?",
    "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
    "questions": [
        {"id": 1, "text": "Feeling nervous, anxious, or on edge"},
        {"id": 2, "text": "Not being able to stop or control worrying"},
        {"id": 3, "text": "Worrying too much about different things"},
        {"id": 4, "text": "Trouble relaxing"},
        {"id": 5, "text": "Being so restless that it is hard to sit still"},
        {"id": 6, "text": "Becoming easily annoyed or irritable"},
        {"id": 7, "text": "Feeling afraid as if something awful might happen"},
    ],
    "scoring_bands": [
        {"max_score": 4, "label": "Minimal"},
        {"max_score": 9, "label": "Mild"},
        {"max_score": 14, "label": "Moderate"},
        {"max_score": 21, "label": "Severe"},
    ],
    "answer_min": 0,
    "answer_max": 3,
    "critical_items": [],
}


async def seed_instruments() -> None:
    async with AsyncSessionLocal() as db:
        for data in (PHQ9, GAD7):
            existing = (
                await db.execute(
                    select(ScreeningInstrument).where(ScreeningInstrument.code == data["code"])
                )
            ).scalars().first()
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
                print(f"Updated instrument: {data['code']}")
            else:
                db.add(ScreeningInstrument(**data))
                print(f"Created instrument: {data['code']}")
        await db.commit()
        print("Screening instruments seeded.")


if __name__ == "__main__":
    asyncio.run(seed_instruments())
