"""
SafeScan — User Model
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """User account model."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # MFA
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)

    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)

    # Role-based access
    role = Column(
        SAEnum("viewer", "operator", "admin", "security_auditor", name="user_role", create_type=False),
        default="viewer",
        nullable=False,
    )

    # Organization membership
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocked_reason = Column(String(500), nullable=True)

    # Login tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Balance
    balance = Column(Float, default=0.0, nullable=False)

    # Free scan allowance
    free_scans_remaining = Column(Integer, default=5, nullable=False)

    # User settings (JSONB)
    settings = Column(JSONB, nullable=True, default=dict)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    domains = relationship("Domain", back_populates="user")
    scans = relationship("Scan", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
