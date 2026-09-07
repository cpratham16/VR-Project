from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin, get_optional_current_user
from app.models.user import User
from app.models.newsletter import Newsletter
from app.schemas.newsletter import NewsletterCreate, NewsletterUpdate, NewsletterResponse

router = APIRouter(prefix="/newsletters", tags=["newsletters"])

@router.post("", response_model=NewsletterResponse, status_code=status.HTTP_201_CREATED)
async def create_newsletter(
    newsletter_in: NewsletterCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    data = newsletter_in.model_dump()
    if data.get("is_published"):
        data["published_at"] = datetime.utcnow()
    newsletter = Newsletter(**data)
    db.add(newsletter)
    await db.commit()
    await db.refresh(newsletter)
    return newsletter

@router.get("", response_model=List[NewsletterResponse])
async def list_newsletters(
    is_published: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = select(Newsletter)

    if not current_user or current_user.role != "admin":
        query = query.where(Newsletter.is_published == True)
    elif is_published is not None:
        query = query.where(Newsletter.is_published == is_published)

    query = query.order_by(Newsletter.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{newsletter_id}", response_model=NewsletterResponse)
async def get_newsletter(
    newsletter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    result = await db.execute(select(Newsletter).where(Newsletter.id == newsletter_id))
    newsletter = result.scalars().first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    if not newsletter.is_published and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Newsletter not found")

    return newsletter

@router.patch("/{newsletter_id}", response_model=NewsletterResponse)
async def update_newsletter(
    newsletter_id: str,
    newsletter_in: NewsletterUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(Newsletter).where(Newsletter.id == newsletter_id))
    newsletter = result.scalars().first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    update_data = newsletter_in.model_dump(exclude_unset=True)
    if update_data.get("is_published") and not newsletter.is_published and not newsletter.published_at:
        update_data["published_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(newsletter, field, value)

    await db.commit()
    await db.refresh(newsletter)
    return newsletter

@router.delete("/{newsletter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_newsletter(
    newsletter_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(Newsletter).where(Newsletter.id == newsletter_id))
    newsletter = result.scalars().first()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter not found")

    await db.delete(newsletter)
    await db.commit()
    return None
