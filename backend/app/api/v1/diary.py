from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc

from app.core.database import get_db
from app.models.user import User
from app.models.diary import DiaryEntry
from app.api.deps import get_current_user
from app.schemas.diary import DiaryEntryCreate, DiaryEntryUpdate, DiaryEntryResponse

router = APIRouter()

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
        entry_date=entry_date
    )
    db.add(db_entry)
    await db.commit()
    await db.refresh(db_entry)
    return db_entry

@router.get("/", response_model=List[DiaryEntryResponse])
async def list_diary_entries(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
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
    
    query = query.order_by(desc(DiaryEntry.entry_date)).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()

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