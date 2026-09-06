from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.core.security import get_password_hash, verify_password

router = APIRouter(prefix="/privacy", tags=["diary_privacy"])

class PinSetupRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8, description="4-8 digit PIN")

class PinVerifyRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=8)

class PinResponse(BaseModel):
    has_pin: bool
    message: str

@router.post("/pin", response_model=PinResponse)
async def setup_diary_pin(
    pin_data: PinSetupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set up or update diary PIN."""
    if current_user.diary_pin_hash:
        raise HTTPException(status_code=400, detail="PIN already set. Use PUT to change.")
    
    current_user.diary_pin_hash = get_password_hash(pin_data.pin)
    await db.commit()
    return PinResponse(has_pin=True, message="Diary PIN set successfully")

@router.put("/pin", response_model=PinResponse)
async def change_diary_pin(
    pin_data: PinSetupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change existing diary PIN."""
    if not current_user.diary_pin_hash:
        raise HTTPException(status_code=400, detail="No PIN set. Use POST to set initial PIN.")
    
    current_user.diary_pin_hash = get_password_hash(pin_data.pin)
    await db.commit()
    return PinResponse(has_pin=True, message="Diary PIN updated successfully")

@router.delete("/pin", response_model=PinResponse)
async def remove_diary_pin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove diary PIN."""
    if not current_user.diary_pin_hash:
        raise HTTPException(status_code=400, detail="No PIN set.")
    
    current_user.diary_pin_hash = None
    await db.commit()
    return PinResponse(has_pin=False, message="Diary PIN removed")

@router.get("/pin/status", response_model=PinResponse)
async def get_pin_status(
    current_user: User = Depends(get_current_user)
):
    """Check if user has a diary PIN set."""
    return PinResponse(
        has_pin=bool(current_user.diary_pin_hash),
        message="PIN status retrieved"
    )

@router.post("/pin/verify")
async def verify_diary_pin(
    pin_data: PinVerifyRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify diary PIN for access."""
    if not current_user.diary_pin_hash:
        raise HTTPException(status_code=400, detail="No PIN set for this account.")
    
    if not verify_password(pin_data.pin, current_user.diary_pin_hash):
        raise HTTPException(status_code=401, detail="Invalid PIN")
    
    return {"verified": True, "message": "PIN verified successfully"}