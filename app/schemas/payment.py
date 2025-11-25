from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreatePaymentIntentRequest(BaseModel):
    user_id: str
    amount: int = Field(..., gt=0, description="Amount in smallest currency unit (e.g., cents)")
    currency: str = Field("usd", description="ISO currency code")
    idempotency_key: Optional[str] = Field(
        None, description="Optional idempotency key to safely retry creation"
    )


class PaymentIntentResponse(BaseModel):
    payment_id: int
    client_secret: str
    status: str


class ConfirmPaymentRequest(BaseModel):
    payment_intent_id: str
    idempotency_key: Optional[str] = Field(
        None, description="Idempotency key ensures repeated confirmation does not double-charge"
    )


class PaymentStatusResponse(BaseModel):
    id: int
    user_id: str
    amount: int
    currency: str
    status: str
    client_secret: str | None = None
    stripe_payment_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
