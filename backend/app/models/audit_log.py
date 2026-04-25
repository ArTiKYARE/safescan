"""
SafeScan — Audit Log Model (Immutable)
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Immutable audit log for compliance and security.
    
    Uses hash chaining (Merkle tree concept) to prevent tampering.
    Each row's hash includes the previous row's hash.
    """

    __tablename__ = "audit_log"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., SCAN_CREATED, LOGIN
    resource_type = Column(String(50), nullable=True)  # e.g., scan, domain, user
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)  # Structured action data

    # Network info
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Hash chain for integrity
    prev_hash = Column(String(64), nullable=True)  # SHA-256 of previous row
    row_hash = Column(String(64), nullable=True, index=True)  # SHA-256 of this row

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id}>"
