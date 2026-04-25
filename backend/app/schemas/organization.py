"""
SafeScan — Organization & API Key Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


# --- Organization ---

class OrganizationCreate(BaseModel):
    """Schema for creating an organization."""
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9\-]+$")
    description: Optional[str] = None
    website: Optional[str] = None
    data_processing_agreement: bool = False
    gdpr_consent: bool = False


class OrganizationResponse(BaseSchema):
    """Organization details response."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    website: Optional[str]
    max_domains: int
    max_concurrent_scans: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- API Key ---

class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: str = Field(default="read", pattern=r"^(read|write|scan|read,write|read,scan|write,scan|read,write,scan)$")
    expires_in_days: Optional[int] = Field(default=90, ge=1, le=365)
    allowed_ips: Optional[str] = None  # CIDR ranges


class APIKeyResponse(BaseSchema):
    """API key response (without secret)."""
    id: str
    name: str
    key_prefix: str
    scopes: str
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyWithSecret(APIKeyResponse):
    """API key response with secret (shown only once)."""
    secret: str  # Full API key secret
