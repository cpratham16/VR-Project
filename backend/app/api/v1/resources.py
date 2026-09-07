from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin, get_optional_current_user
from app.models.user import User
from app.models.resource import Resource, UserResourceProgress
from app.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceProgressUpdate, ResourceProgressResponse, ResourceWithProgressResponse
)

router = APIRouter(prefix="/resources", tags=["resources"])

@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_in: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    resource = Resource(**resource_in.model_dump())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource

@router.get("", response_model=List[ResourceResponse])
async def list_resources(
    category: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    query = select(Resource)

    # Non-admins can only see published resources
    if not current_user or current_user.role != "admin":
        query = query.where(Resource.is_published == True)
    elif is_published is not None:
        query = query.where(Resource.is_published == is_published)

    if category:
        query = query.where(Resource.category == category)
    if resource_type:
        query = query.where(Resource.resource_type == resource_type)

    query = query.order_by(Resource.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/my-library", response_model=List[ResourceWithProgressResponse])
async def get_my_library(
    saved_only: Optional[bool] = Query(False),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Resource).where(Resource.is_published == True)
    if category:
        query = query.where(Resource.category == category)
    query = query.order_by(Resource.created_at.desc())
    res_result = await db.execute(query)
    resources = res_result.scalars().all()

    # Load progress for user
    prog_result = await db.execute(
        select(UserResourceProgress).where(UserResourceProgress.user_id == current_user.id)
    )
    progress_map = {p.resource_id: p for p in prog_result.scalars().all()}

    output = []
    for r in resources:
        prog = progress_map.get(r.id)
        if saved_only and (not prog or not prog.saved_for_later):
            continue
        output.append(
            ResourceWithProgressResponse(
                id=r.id,
                title=r.title,
                description=r.description,
                resource_type=r.resource_type,
                category=r.category,
                file_url=r.file_url,
                thumbnail_url=r.thumbnail_url,
                author=r.author,
                is_published=r.is_published,
                created_at=r.created_at,
                updated_at=r.updated_at,
                progress=ResourceProgressResponse.model_validate(prog) if prog else None
            )
        )
    return output

@router.post("/{resource_id}/progress", response_model=ResourceProgressResponse)
async def update_resource_progress(
    resource_id: str,
    progress_in: ResourceProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify resource exists and is published
    res_check = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = res_check.scalars().first()
    if not resource or not resource.is_published:
        raise HTTPException(status_code=404, detail="Resource not found")

    prog_query = await db.execute(
        select(UserResourceProgress).where(
            UserResourceProgress.user_id == current_user.id,
            UserResourceProgress.resource_id == resource_id
        )
    )
    progress = prog_query.scalars().first()
    if not progress:
        progress = UserResourceProgress(
            user_id=current_user.id,
            resource_id=resource_id
        )
        db.add(progress)

    if progress_in.saved_for_later is not None:
        progress.saved_for_later = progress_in.saved_for_later
    if progress_in.progress_percent is not None:
        progress.progress_percent = max(0, min(100, progress_in.progress_percent))
        if progress.progress_percent == 100:
            progress.is_completed = True
    if progress_in.is_completed is not None:
        progress.is_completed = progress_in.is_completed
        if progress.is_completed:
            progress.progress_percent = 100

    await db.commit()
    await db.refresh(progress)
    return progress

@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if not resource.is_published and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource

@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: str,
    resource_in: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    update_data = resource_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)

    await db.commit()
    await db.refresh(resource)
    return resource

@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin)
):
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    await db.delete(resource)
    await db.commit()
    return None
