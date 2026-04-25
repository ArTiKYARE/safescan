"""
SafeScan — Notification Model
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Notification preferences and delivery history."""

    __tablename__ = "notifications"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Type
    notification_type = Column(
        SAEnum(
            "scan_completed",
            "vulnerability_found",
            "critical_finding",
            "verification_required",
            "account_security",
            name="notification_type",
        ),
        nullable=False,
    )

    # Delivery channels
    channel = Column(
        SAEnum("email", "webhook", "slack", name="notification_channel", create_type=False),
        nullable=False,
    )
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Channel-specific config
    config = Column(JSONB, nullable=True)
    # Email: { }
    # Webhook: { "url": "https://...", "secret": "..." }
    # Slack: { "webhook_url": "https://hooks.slack.com/...", "channel": "#security" }

    # Delivery tracking
    last_sent_at = None
    last_delivery_status = Column(String(20), nullable=True)  # success, failed
    last_error = Column(Text, nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<Notification {self.notification_type} via {self.channel}>"
