from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.community import CommunityPost, CommunityComment
from app.api.deps import get_current_doctor
from app.schemas.community import CommunityPostResponse, ModerationActionRequest

router = APIRouter()

@router.get("/queue", response_model=List[CommunityPostResponse])
async def get_moderation_queue(
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    query = await db.execute(
        select(CommunityPost)
        .options(selectinload(CommunityPost.comments))
        .where(CommunityPost.moderation_status == "flagged_pending")
        .order_by(CommunityPost.created_at.desc())
    )
    posts = query.scalars().all()

    res_list = []
    for post in posts:
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
            "comment_count": len(post.comments),
            "comments": post.comments
        })

    return res_list

@router.post("/posts/{post_id}/action")
async def moderate_post_action(
    post_id: str,
    action_in: ModerationActionRequest,
    db: AsyncSession = Depends(get_db),
    current_doctor: User = Depends(get_current_doctor)
):
    query = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = query.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if action_in.action.lower() == "approve":
        post.moderation_status = "approved"
    elif action_in.action.lower() == "reject":
        post.moderation_status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    await db.commit()
    await db.refresh(post)
    return {"status": post.moderation_status, "message": f"Post moderation action '{action_in.action}' applied successfully"}
