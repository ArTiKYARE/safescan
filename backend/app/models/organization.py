"""
SafeScan — Organization Model
"""

from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Organization / Company model for multi-tenancy."""

    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)

    # Settings
    max_domains = Column(Integer, default=5, nullable=False)
    max_concurrent_scans = Column(Integer, default=10, nullable=False)

    # Compliance
    data_processing_agreement = Column(Boolean, default=False, nullable=False)
    gdpr_consent = Column(Boolean, default=False, nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization")
    domains = relationship("Domain", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.name}>"
