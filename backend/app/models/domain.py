"""
SafeScan — Domain Model
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Domain(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Domain that has been added for verification and scanning."""

    __tablename__ = "domains"

    domain = Column(String(255), nullable=False, index=True)
    
    # Ownership verification
    verification_method = Column(
        SAEnum("dns", "file", "email", "api_token", name="verification_method", create_type=False),
        nullable=True,
    )
    verification_token = Column(String(255), nullable=True)
    api_verification_token = Column(String(255), nullable=True, unique=True, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    last_reverification = Column(DateTime(timezone=True), nullable=True)
    reverification_required = Column(Boolean, default=False, nullable=False)

    # DNS verification details
    dns_record_name = Column(String(100), nullable=True)  # _safescan-verify
    dns_record_value = Column(String(255), nullable=True)

    # File verification details
    verification_file_path = Column(String(255), nullable=True)  # /.well-known/safescan-verify.txt

    # Email verification details
    verification_email_sent_to = Column(String(255), nullable=True)
    verification_email_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Ownership
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scan settings
    scan_consent_required = Column(Boolean, default=True, nullable=False)
    custom_user_agent = Column(String(255), nullable=True)
    excluded_paths = Column(Text, nullable=True)  # JSON array of path patterns

    # Relationships
    user = relationship("User", back_populates="domains")
    organization = relationship("Organization", back_populates="domains")
    scans = relationship("Scan", back_populates="domain", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Domain {self.domain} (verified={self.is_verified})>"
