from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.patient import PatientProfile
from app.models.community import CommunityPost, CommunityComment
from app.models.alert import RiskAlert
from app.api.deps import get_current_user
from app.schemas.community import (
    CommunityPostCreate, CommunityPostResponse,
    CommunityCommentCreate, CommunityCommentResponse
)
from app.services.risk_engine import risk_engine_service

router = APIRouter()

@router.get("/posts", response_model=List[CommunityPostResponse])
async def get_community_posts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(CommunityPost).options(selectinload(CommunityPost.comments)).where(
        CommunityPost.moderation_status == "approved"
    )

    if category and category.lower() != "all":
        query = query.where(CommunityPost.category == category)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (CommunityPost.title.ilike(search_pattern)) | (CommunityPost.content.ilike(search_pattern))
        )

    query = query.order_by(CommunityPost.created_at.desc())
    result = await db.execute(query)
    posts = result.scalars().all()

    res_list = []
    for post in posts:
        approved_comments = [c for c in post.comments if c.moderation_status == "approved"]
        res_list.append({
            "id": post.id,
            "author_pseudonym": post.author_pseudonym,
            "category": post.category,
            "title": post.title,
            "content": post.content,
            "is_flagged": post.is_flagged,
            "moderation_status": post.moderation_status,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "comment_count": len(approved_comments),
            "comments": approved_comments
        })

    return res_list

@router.post("/posts", response_model=CommunityPostResponse)
async def create_community_post(
    post_in: CommunityPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not post_in.title.strip() or not post_in.content.strip():
        raise HTTPException(status_code=400, detail="Title and content are required")

    # Fetch patient pseudonym
    p_query = await db.execute(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    patient = p_query.scalars().first()
    author_pseudonym = patient.pseudonym if patient else "Anonymous Student"

    # Scan for distress keywords
    full_text = f"{post_in.title} {post_in.content}"
    is_flagged, severity = risk_engine_service.scan_message_for_distress(full_text)

    status = "flagged_pending" if is_flagged else "approved"

    db_post = CommunityPost(
        user_id=current_user.id,
        author_pseudonym=author_pseudonym,
        category=post_in.category or "General Wellness",
        title=post_in.title.strip(),
        content=post_in.content.strip(),
        is_flagged=is_flagged,
        moderation_status=status
    )
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)

    if is_flagged:
        alert = RiskAlert(
            user_id=current_user.id,
            severity=severity,
            trigger_source="community_post_flag",
            details=f"Community Post Flagged: Title '{db_post.title}'"
        )
        db.add(alert)
        await db.commit()

    return {
        "id": db_post.id,
        "author_pseudonym": db_post.author_pseudonym,
        "category": db_post.category,
        "title": db_post.title,
        "content": db_post.content,
        "is_flagged": db_post.is_flagged,
        "moderation_status": db_post.moderation_status,
        "created_at": db_post.created_at,
        "updated_at": db_post.updated_at,
        "comment_count": 0,
        "comments": []
    }

@router.get("/posts/{post_id}", response_model=CommunityPostResponse)
async def get_community_post(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = await db.execute(
        select(CommunityPost)
        .options(selectinload(CommunityPost.comments))
        .where(CommunityPost.id == post_id)
    )
    post = query.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    approved_comments = [c for c in post.comments if c.moderation_status == "approved"]

    return {
        "id": post.id,
        "author_pseudonym": post.author_pseudonym,
        "category": post.category,
        "title": post.title,
        "content": post.content,
        "is_flagged": post.is_flagged,
        "moderation_status": post.moderation_status,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "comment_count": len(approved_comments),
        "comments": approved_comments
    }

@router.post("/posts/{post_id}/comments", response_model=CommunityCommentResponse)
async def add_post_comment(
    post_id: str,
    comment_in: CommunityCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not comment_in.content.strip():
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")

    query = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = query.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    p_query = await db.execute(select(PatientProfile).where(PatientProfile.user_id == current_user.id))
    patient = p_query.scalars().first()
    author_pseudonym = patient.pseudonym if patient else "Anonymous Student"

    is_flagged, severity = risk_engine_service.scan_message_for_distress(comment_in.content)
    status = "flagged_pending" if is_flagged else "approved"

    db_comment = CommunityComment(
        post_id=post.id,
        user_id=current_user.id,
        author_pseudonym=author_pseudonym,
        content=comment_in.content.strip(),
        is_flagged=is_flagged,
        moderation_status=status
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)

    if is_flagged:
        alert = RiskAlert(
            user_id=current_user.id,
            severity=severity,
            trigger_source="community_comment_flag",
            details=f"Community Comment Flagged: '{db_comment.content[:50]}...'"
        )
        db.add(alert)
        await db.commit()

    return db_comment
