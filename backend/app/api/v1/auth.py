import json
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.token import Token
from app.api.deps import get_current_user

router = APIRouter()


async def _serialize_user(db: AsyncSession, user: User) -> dict:
    has_credentials = False
    review_status = "approved"
    rejection_reason = None
    specialty = None
    languages = None
    if user.role == "doctor":
        profile = (
            await db.execute(
                select(DoctorProfile).where(DoctorProfile.user_id == user.id)
            )
        ).scalars().first()
        has_credentials = bool(profile and profile.credential_filename)
        if profile:
            review_status = profile.review_status or ("approved" if user.is_verified else "pending")
            rejection_reason = profile.rejection_reason
            specialty = profile.specialty
            languages = profile.languages_list
        else:
            review_status = "approved" if user.is_verified else "pending"
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "state": user.state,
        "city": user.city,
        "full_name": user.full_name,
        "phone": user.phone,
        "emergency_contact_phone": user.emergency_contact_phone,
        "has_credentials": has_credentials,
        "review_status": review_status,
        "rejection_reason": rejection_reason,
        "specialty": specialty,
        "languages": languages,
    }


@router.post("/signup", response_model=UserResponse)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if user_in.role not in ("patient", "doctor"):
        raise HTTPException(
            status_code=400,
            detail="Self-registration is only available for patient and doctor accounts. Admin accounts must be created by an existing administrator.",
        )
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()

    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )

    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        state=user_in.state,
        city=user_in.city,
        full_name=user_in.full_name,
        phone=user_in.phone,
        emergency_contact_phone=user_in.emergency_contact_phone
    )
    db.add(db_user)
    await db.flush()

    if user_in.role == "doctor":
        if not user_in.license_number or not user_in.license_number.strip():
            raise HTTPException(
                status_code=400,
                detail="Doctors must provide a license / registration number",
            )
        db.add(DoctorProfile(
            user_id=db_user.id,
            license_number=user_in.license_number.strip(),
            specialty=(user_in.specialty or None),
            languages=json.dumps(user_in.languages or []),
        ))

    await db.commit()
    await db.refresh(db_user)
    return await _serialize_user(db, db_user)

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await _serialize_user(db, current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name.strip() or None
    if user_in.phone is not None:
        current_user.phone = (user_in.phone or "").strip() or None
    if user_in.emergency_contact_phone is not None:
        current_user.emergency_contact_phone = (user_in.emergency_contact_phone or "").strip() or None
    if user_in.state is not None:
        current_user.state = (user_in.state or "").strip() or None
    if user_in.city is not None:
        current_user.city = (user_in.city or "").strip() or None

    if current_user.role == "doctor":
        if user_in.specialty is not None or user_in.languages is not None:
            profile = (
                await db.execute(
                    select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
                )
            ).scalars().first()
            if not profile:
                raise HTTPException(status_code=404, detail="Doctor profile not found")
            if user_in.specialty is not None:
                profile.specialty = (user_in.specialty or "").strip() or None
            if user_in.languages is not None:
                profile.languages = json.dumps(user_in.languages or [])

    await db.commit()
    await db.refresh(current_user)
    return await _serialize_user(db, current_user)
