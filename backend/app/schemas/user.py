"""
SafeScan — User Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.schemas.base import BaseSchema


# --- Request Schemas ---

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str
    mfa_token: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class EmailVerification(BaseModel):
    """Schema for email verification."""
    token: str


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class MFASetup(BaseModel):
    """Schema for MFA setup initiation."""
    pass


class MFAVerify(BaseModel):
    """Schema for MFA verification."""
    totp_code: str = Field(..., min_length=6, max_length=6)


# --- Response Schemas ---

class UserResponse(BaseSchema):
    """User profile response."""
    id: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    mfa_enabled: bool
    email_verified: bool
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    # Balance
    balance: float = 0.0
    free_scans_remaining: int = 0

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
