from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.alert import RiskAlert
from app.api.deps import get_current_user
from app.schemas.alert import PanicRequest, RiskAlertResponse

router = APIRouter()

@router.post("", response_model=RiskAlertResponse)
async def trigger_panic_sos(
    panic_in: PanicRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Log critical emergency alert for doctor notification
    alert = RiskAlert(
        user_id=current_user.id,
        severity="CRITICAL",
        trigger_source="panic_sos",
        details=f"One-Tap Panic SOS Triggered. Location Note: {panic_in.location_note or 'Campus Premises'}"
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert
