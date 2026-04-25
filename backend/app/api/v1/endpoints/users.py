"""
SafeScan — Users Endpoints
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user, hash_password, verify_password, require_role
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, PasswordChange
from app.services.audit import log_audit_event

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/role")
async def get_my_role(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user role."""
    return {
        "user_id": current_user.get("sub"),
        "role": current_user.get("role", "viewer"),
        "is_admin": current_user.get("role") in ("admin", "security_auditor"),
    }


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    if user_data.last_name is not None:
        user.last_name = user_data.last_name

    await log_audit_event(
        db=db,
        user_id=user.id,
        action="PROFILE_UPDATED",
    )

    await db.commit()
    await db.refresh(user)
    return user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.password_hash = hash_password(password_data.new_password)

    await log_audit_event(
        db=db,
        user_id=user.id,
        action="PASSWORD_CHANGED",
    )

    await db.commit()
    return {"message": "Password changed successfully"}
