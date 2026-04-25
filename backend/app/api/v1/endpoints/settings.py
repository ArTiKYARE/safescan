"""
SafeScan — Settings Endpoints
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.audit import log_audit_event

router = APIRouter()

DEFAULT_SETTINGS = {
    "notifications": {
        "email": True,
        "webhook": False,
        "slack": False,
    },
    "scan_defaults": {
        "scan_type": "full",
        "consent_required": True,
    },
}


@router.get("/")
async def get_settings(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user settings."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return stored settings or defaults
    settings = user.settings or DEFAULT_SETTINGS
    return settings


@router.put("/")
async def update_settings(
    settings_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user settings."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Merge with existing settings
    existing = user.settings or {}
    existing.update(settings_data)
    user.settings = existing

    await log_audit_event(
        db=db,
        user_id=user.id,
        action="SETTINGS_UPDATED",
        details={"keys_updated": list(settings_data.keys())},
    )

    await db.commit()
    return {"message": "Settings updated", "settings": existing}
