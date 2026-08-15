from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.models.mood import MoodEntry
from app.api.deps import get_current_user
from app.schemas.mood import MoodEntryCreate, MoodEntryUpdate, MoodEntryResponse

router = APIRouter()

@router.post("/", response_model=MoodEntryResponse)
async def create_mood_entry(
    entry_in: MoodEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_entry = MoodEntry(
        user_id=current_user.id,
        mood_score=entry_in.mood_score,
        tags=entry_in.tags,
        journal_text=entry_in.journal_text
    )
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    
    resp = MoodEntryResponse.model_validate(db_entry)
    resp.can_edit = True
    return resp

@router.get("/history", response_model=List[MoodEntryResponse])
async def get_mood_history(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = await db.execute(
        select(MoodEntry)
        .where(
            MoodEntry.user_id == current_user.id,
            MoodEntry.created_at >= cutoff
        )
        .order_by(MoodEntry.created_at.desc())
    )
    entries = query.scalars().all()
    
    now = datetime.utcnow()
    results = []
    for e in entries:
        item = MoodEntryResponse.model_validate(e)
        # Edit window: 24 hours
        item.can_edit = (now - e.created_at) <= timedelta(hours=24)
        results.append(item)
        
    return results

@router.put("/{entry_id}", response_model=MoodEntryResponse)
async def update_mood_entry(
    entry_id: str,
    entry_in: MoodEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(MoodEntry).where(
            MoodEntry.id == entry_id,
            MoodEntry.user_id == current_user.id
        )
    )
    db_entry = query.scalars().first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Mood entry not found")
        
    now = datetime.utcnow()
    if (now - db_entry.created_at) > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="Entries can only be edited within 24 hours of creation")

    if entry_in.mood_score is not None:
        db_entry.mood_score = entry_in.mood_score
    if entry_in.tags is not None:
        db_entry.tags = entry_in.tags
    if entry_in.journal_text is not None:
        db_entry.journal_text = entry_in.journal_text
        
    db_entry.updated_at = now
    await db.commit()
    await db.refresh(db_entry)
    
    resp = MoodEntryResponse.model_validate(db_entry)
    resp.can_edit = True
    return resp
