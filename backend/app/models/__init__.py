"""
SafeScan — SQLAlchemy Models
"""
# This file imports all models to register them with Base.metadata

from app.models.user import User
from app.models.organization import Organization
from app.models.domain import Domain
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.models.audit_log import AuditLog
from app.models.api_key import APIKey
from app.models.notification import Notification
from app.models.transaction import Transaction

__all__ = [
    "User",
    "Organization",
    "Domain",
    "Scan",
    "Vulnerability",
    "AuditLog",
    "APIKey",
    "Notification",
    "Transaction",
]
