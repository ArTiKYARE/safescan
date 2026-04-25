"""
SafeScan — API Keys Endpoints
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.api_key import APIKey
from app.schemas.organization import APIKeyCreate, APIKeyResponse, APIKeyWithSecret

router = APIRouter()


@router.post("/", response_model=APIKeyWithSecret, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key."""
    # Generate secret
    secret = f"ss_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(secret.encode()).hexdigest()
    key_prefix = secret[:12]

    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=key_data.expires_in_days
        )

    new_key = APIKey(
        user_id=uuid.UUID(current_user["sub"]),
        name=key_data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        secret=secret,  # Store for first display
        scopes=key_data.scopes,
        allowed_ips=key_data.allowed_ips,
        expires_at=expires_at,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    response = APIKeyWithSecret(
        id=str(new_key.id),
        name=new_key.name,
        key_prefix=new_key.key_prefix,
        scopes=new_key.scopes,
        expires_at=new_key.expires_at,
        last_used_at=new_key.last_used_at,
        is_active=new_key.is_active,
        created_at=new_key.created_at,
        secret=secret,  # Only returned here, never again
    )
    return response


@router.get("/", response_model=list[APIKeyWithSecret])
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for current user."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == uuid.UUID(current_user["sub"]))
        .order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key permanently."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == uuid.UUID(key_id),
            APIKey.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(key)
    await db.commit()
