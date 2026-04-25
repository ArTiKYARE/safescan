"""
SafeScan — API Key Authentication
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.api_key import APIKey
from app.models.user import User

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


async def get_current_user_by_api_key(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Authenticate user via API key from X-API-Key header.

    Returns the same dict structure as JWT auth (sub, email, role).
    """
    if not api_key:
        return {}  # No API key provided — let JWT auth handle it

    # Hash the incoming key for comparison
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Look up by key_hash with row-level lock
    result = await db.execute(
        select(APIKey)
        .where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
            APIKey.is_revoked == False,
        )
        .with_for_update()
    )
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check expiry
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Update usage stats
    api_key_obj.usage_count += 1
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    # Get the owner user
    user_result = await db.execute(
        select(User).where(User.id == api_key_obj.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Parse scopes
    scopes = set(api_key_obj.scopes.split(",")) if api_key_obj.scopes else {"read"}

    # Return user payload compatible with JWT auth
    return {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "auth_method": "api_key",
        "scopes": scopes,
    }
