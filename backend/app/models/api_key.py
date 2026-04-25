"""
SafeScan — API Key Model
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class APIKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """API keys for programmatic access."""

    __tablename__ = "api_keys"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(100), nullable=False)  # User-friendly name
    key_prefix = Column(String(12), nullable=False, index=True)  # First 12 chars for lookup
    key_hash = Column(String(255), unique=True, nullable=False)  # SHA-256 hash of full key
    secret = Column(String(255), nullable=True)  # Full secret (shown only once at creation)

    # Permissions
    scopes = Column(String(255), default="read")  # Comma-separated: read,write,scan
    allowed_ips = Column(String(500), nullable=True)  # CIDR ranges, null = any

    # Lifecycle
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    # Usage tracking
    usage_count = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey {self.name} ({self.key_prefix}...)>"
