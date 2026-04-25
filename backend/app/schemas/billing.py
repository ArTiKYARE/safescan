"""
SafeScan — Billing Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


class BalanceResponse(BaseModel):
    balance: float
    currency: str = "RUB"


class TopUpRequest(BaseModel):
    amount: float = Field(..., gt=0, le=1000000, description="Сумма пополнения в рублях")


class TransactionResponse(BaseSchema):
    id: str
    amount: float
    currency: str
    type: str
    status: str
    payment_method: Optional[str] = None
    description: Optional[str] = None
    confirmation_url: Optional[str] = None
    created_at: datetime


class AdminTopUpRequest(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0, le=1000000, description="Сумма пополнения в рублях")
    description: Optional[str] = None
