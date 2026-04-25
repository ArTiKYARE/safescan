"""
SafeScan — Scan Model
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Scan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single vulnerability scan execution."""

    __tablename__ = "scans"

    domain_id = Column(
        UUID(as_uuid=True),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )

    # Scan configuration
    scan_type = Column(
        SAEnum("full", "quick", "custom", name="scan_type", create_type=False),
        default="full",
        nullable=False,
    )
    modules_enabled = Column(JSONB, nullable=True)  # Array of module names
    modules_disabled = Column(JSONB, nullable=True)  # Excluded modules

    # Status & timing
    status = Column(
        SAEnum(
            "pending",
            "queued",
            "running",
            "completed",
            "failed",
            "cancelled",
            name="scan_status",
            create_type=False,
        ),
        default="pending",
        nullable=False,
        index=True,
    )
    celery_task_id = Column(
        String(255), nullable=True
    )  # Celery task ID for cancellation
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)

    # Progress tracking
    current_module = Column(String(100), nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)
    pages_crawled = Column(Integer, default=0, nullable=False)
    requests_made = Column(Integer, default=0, nullable=False)

    # Results summary
    total_findings = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    low_count = Column(Integer, default=0, nullable=False)
    info_count = Column(Integer, default=0, nullable=False)
    risk_score = Column(Float, nullable=True)  # 0-10
    grade = Column(String(2), nullable=True)  # A+, A, B, C, D, F

    # Consent & compliance
    consent_acknowledged = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime(timezone=True), nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Report storage
    report_json_path = Column(String(500), nullable=True)  # S3 key
    report_pdf_path = Column(String(500), nullable=True)
    report_html_path = Column(String(500), nullable=True)

    # Relationships
    domain = relationship("Domain", back_populates="scans")
    user = relationship("User", back_populates="scans")
    vulnerabilities = relationship(
        "Vulnerability",
        back_populates="scan",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Scan {self.id} ({self.status})>"
