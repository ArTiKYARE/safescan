"""
SafeScan — API Key Schemas
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100, description="User-friendly name")
    scopes: Optional[str] = Field(default="read", description="Comma-separated scopes")
    allowed_ips: Optional[str] = Field(default=None, description="Allowed CIDR ranges")
    expires_at: Optional[datetime] = Field(default=None, description="Key expiration time")


class APIKeyResponse(BaseSchema):
    """Public API key response (no secret)."""
    id: str
    name: str
    key_prefix: str
    secret: Optional[str] = None  # Only shown once at creation, null afterwards
    scopes: Optional[str] = None
    is_active: bool
    is_revoked: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    usage_count: int

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API key response including the secret (shown only once)."""
    secret: str = Field(..., description="Full API key secret (shown only once)")
