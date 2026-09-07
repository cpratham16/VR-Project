from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin, get_optional_current_user
from app.models.user import User
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, ResourceUpdate, ResourceResponse

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
