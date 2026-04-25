"""
SafeScan — Domain Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


class DomainCreate(BaseModel):
    """Schema for adding a domain for verification."""

    domain: str = Field(
        ...,
        min_length=3,
        max_length=255,
        pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$",
    )
    verification_method: str = Field(
        default="api_token",
        pattern="^(dns|file|api_token)$",
        description="Verification method: dns, file, or api_token",
    )


class DomainVerify(BaseModel):
    """Schema for triggering domain verification check."""

    pass


class DomainResponse(BaseSchema):
    """Domain details response."""

    id: str
    domain: str
    is_verified: bool
    verification_method: Optional[str]
    verified_at: Optional[datetime]
    scan_consent_required: bool
    created_at: datetime
    updated_at: datetime
    # API key fields (for api_token verification method)
    api_key: Optional[str] = None
    api_key_prefix: Optional[str] = None
    env_line: Optional[str] = None
    _regenerated: Optional[bool] = None

    class Config:
        from_attributes = True


class DomainVerificationStatus(BaseModel):
    """Domain verification status."""

    domain_id: str
    domain: str
    is_verified: bool
    verification_method: Optional[str]
    verification_token: Optional[str]
    dns_record_name: Optional[str]
    dns_record_value: Optional[str]
    verification_file_path: Optional[str]
    verification_email_sent_to: Optional[str]
    instructions: str
