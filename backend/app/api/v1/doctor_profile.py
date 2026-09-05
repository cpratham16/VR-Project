import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.api.deps import get_current_doctor

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


async def _get_own_profile(db: AsyncSession, user: User) -> DoctorProfile:
    profile = (
        await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))
    ).scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return profile


@router.get("")
async def get_my_doctor_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    if current_user.role != "doctor":
        return {"has_credentials": True, "review_status": "approved", "rejection_reason": None, "profile": None}
    try:
        profile = await _get_own_profile(db, current_user)
    except HTTPException:
        return {"has_credentials": False, "review_status": "pending", "rejection_reason": None, "profile": None}
    return {
        "has_credentials": bool(profile.credential_filename),
        "review_status": profile.review_status or ("approved" if current_user.is_verified else "pending"),
        "rejection_reason": profile.rejection_reason,
        "is_verified": current_user.is_verified,
        "profile": {
            "license_number": profile.license_number,
            "specialty": profile.specialty,
            "languages": profile.languages_list,
            "credential_filename": profile.credential_filename,
            "uploaded_at": profile.uploaded_at,
        },
    }


@router.post("/credential")
async def upload_credential(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctor accounts upload credentials")

    ext = ALLOWED_CONTENT_TYPES.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="Only PDF, JPEG, or PNG files are accepted")

    contents = await file.read()
    max_bytes = settings.CREDENTIAL_MAX_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the {settings.CREDENTIAL_MAX_SIZE_MB} MB limit",
        )

    profile = await _get_own_profile(db, current_user)

    upload_dir = settings.CREDENTIAL_UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, stored_name)
    with open(file_path, "wb") as f:
        f.write(contents)

    if profile.credential_path and os.path.exists(profile.credential_path):
        try:
            os.remove(profile.credential_path)
        except OSError:
            pass

    profile.credential_filename = file.filename or stored_name
    profile.credential_path = file_path
    from datetime import datetime
    profile.uploaded_at = datetime.utcnow()
    profile.review_status = "pending"
    profile.rejection_reason = None
    await db.commit()
    await db.refresh(profile)

    return {
        "message": "Credential document uploaded. Pending admin verification.",
        "review_status": profile.review_status,
        "credential_filename": profile.credential_filename,
        "uploaded_at": profile.uploaded_at,
    }


@router.get("/credential/download", response_class=FileResponse)
async def download_my_credential(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_doctor),
):
    profile = await _get_own_profile(db, current_user)
    if not profile.credential_path or not os.path.exists(profile.credential_path):
        raise HTTPException(status_code=404, detail="No credential document on file")
    return FileResponse(
        profile.credential_path,
        filename=profile.credential_filename or "credential",
    )
