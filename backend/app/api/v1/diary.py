from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, or_
import os
import httpx

from app.core.database import get_db
from app.models.user import User
from app.models.diary import DiaryEntry
from app.api.deps import get_current_user
from app.schemas.diary import DiaryEntryCreate, DiaryEntryUpdate, DiaryEntryResponse
from app.core.config import settings

router = APIRouter()

# Diary AI Reflection prompt
REFLECTION_SYSTEM_PROMPT = """You are a compassionate AI companion providing a gentle, supportive reflection on a personal diary entry. 

Guidelines:
- Be empathetic, warm, and non-judgmental
- Offer supportive insights or gentle reframing
- Suggest healthy coping strategies if relevant
- Keep response to 3-5 sentences
- Never diagnose, prescribe, or give clinical advice
- If content suggests crisis/self-harm, gently encourage professional help
- Respect the user's privacy - this is their personal reflection"""

async def generate_diary_reflection(content: str, title: Optional[str] = None) -> str:
    """Generate AI reflection on a diary entry using Groq API."""
    groq_api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not groq_api_key or len(groq_api_key.strip()) <= 5:
        return "I hear you. Your thoughts and feelings matter. Take a moment to breathe and be kind to yourself today."

    user_prompt = f"Diary entry"
    if title:
        user_prompt += f" titled '{title}'"
    user_prompt += f":\n\n{content}\n\nPlease offer a brief, compassionate reflection."

    try:
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        messages = [
            {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 200
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return "I hear you. Your thoughts and feelings matter. Take a moment to breathe and be kind to yourself today."

@router.post("/", response_model=DiaryEntryResponse)
async def create_diary_entry(
    entry_in: DiaryEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry_date = entry_in.entry_date or datetime.utcnow()
    
    db_entry = DiaryEntry(
        user_id=current_user.id,
        title=entry_in.title,
        content=entry_in.content,
        entry_date=entry_date,
        emotion_tag=entry_in.emotion_tag
    )
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry

@router.get("/", response_model=List[DiaryEntryResponse])
async def list_diary_entries(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    q: Optional[str] = Query(None, description="Search keyword in title and content"),
    emotion_tag: Optional[str] = Query(None, description="Filter by emotion tag"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(DiaryEntry).where(DiaryEntry.user_id == current_user.id)
    
    if start_date:
        query = query.where(DiaryEntry.entry_date >= start_date)
    if end_date:
        query = query.where(DiaryEntry.entry_date <= end_date)
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                DiaryEntry.title.ilike(search_term),
                DiaryEntry.content.ilike(search_term)
            )
        )
    if emotion_tag:
        query = query.where(DiaryEntry.emotion_tag == emotion_tag)
    
    query = query.order_by(desc(DiaryEntry.entry_date)).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


# J7: Streak endpoint
class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    last_entry_date: Optional[str]

@router.get("/streak", response_model=StreakResponse)
async def get_diary_streak(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current and longest journaling streak for the user."""
    query = await db.execute(
        select(DiaryEntry.entry_date)
        .where(DiaryEntry.user_id == current_user.id)
        .order_by(DiaryEntry.entry_date.desc())
    )
    entries = query.scalars().all()
    
    if not entries:
        return StreakResponse(current_streak=0, longest_streak=0, last_entry_date=None)
    
    # Convert to date objects (ignore time)
    entry_dates = sorted(set(e.date() for e in entries))
    
    # Calculate streaks
    current_streak = 0
    longest_streak = 0
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    # Check if there's an entry today or yesterday to start current streak
    if entry_dates[-1] == today or entry_dates[-1] == yesterday:
        current_streak = 1
        for i in range(len(entry_dates) - 2, -1, -1):
            if entry_dates[i+1] - entry_dates[i] == timedelta(days=1):
                current_streak += 1
            else:
                break
    else:
        current_streak = 0
    
    # Longest streak (scan all dates)
    streak = 1
    longest_streak = 1
    for i in range(1, len(entry_dates)):
        if entry_dates[i] - entry_dates[i-1] == timedelta(days=1):
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 1
    
    return StreakResponse(
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_entry_date=entry_dates[-1].isoformat() if entry_dates else None
    )

@router.get("/{entry_id}", response_model=DiaryEntryResponse)
async def get_diary_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(DiaryEntry).where(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        )
    )
    db_entry = query.scalars().first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    return db_entry

@router.put("/{entry_id}", response_model=DiaryEntryResponse)
async def update_diary_entry(
    entry_id: str,
    entry_in: DiaryEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(DiaryEntry).where(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        )
    )
    db_entry = query.scalars().first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    if entry_in.title is not None:
        db_entry.title = entry_in.title
    if entry_in.content is not None:
        db_entry.content = entry_in.content
    if entry_in.entry_date is not None:
        db_entry.entry_date = entry_in.entry_date
    if entry_in.emotion_tag is not None:
        db_entry.emotion_tag = entry_in.emotion_tag
    
    db_entry.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_entry)
    return db_entry

@router.delete("/{entry_id}")
async def delete_diary_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(DiaryEntry).where(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        )
    )
    db_entry = query.scalars().first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    await db.delete(db_entry)
    await db.commit()
    return {"message": "Diary entry deleted"}


# J6: AI Reflection endpoint
from pydantic import BaseModel

class ReflectionResponse(BaseModel):
    entry_id: str
    reflection: str

@router.post("/{entry_id}/reflect", response_model=ReflectionResponse)
async def reflect_on_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI reflection on a specific diary entry (opt-in, per-entry)."""
    query = await db.execute(
        select(DiaryEntry).where(
            DiaryEntry.id == entry_id,
            DiaryEntry.user_id == current_user.id
        )
    )
    db_entry = query.scalars().first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    reflection = await generate_diary_reflection(db_entry.content, db_entry.title)
    return ReflectionResponse(entry_id=entry_id, reflection=reflection)