"""
SafeScan — Transaction Model
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Financial transaction model."""

    __tablename__ = "transactions"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Amount (positive = top-up, negative = spend)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB", nullable=False)

    # Transaction type
    type = Column(
        SAEnum("deposit", "yookassa", "scan_cost", "admin_adjustment", "refund", name="transaction_type", create_type=False),
        nullable=False,
    )

    # Status
    status = Column(
        SAEnum("pending", "completed", "failed", "refunded", name="transaction_status", create_type=False),
        default="pending",
        nullable=False,
        index=True,
    )

    # Payment provider details
    payment_method = Column(String(50), nullable=True)  # yookassa, manual
    payment_id = Column(String(255), nullable=True)  # YooKassa payment.id
    confirmation_url = Column(Text, nullable=True)  # YooKassa confirmation URL

    # Description
    description = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.id} {self.type} {self.amount}>"
