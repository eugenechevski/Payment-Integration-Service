from functools import partial
from typing import Optional

import stripe
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

stripe.api_key = settings.stripe_api_key


async def create_payment_intent(
    user_id: str, amount: int, currency: str = "usd", idempotency_key: Optional[str] = None
):
    create = partial(
        stripe.PaymentIntent.create,
        amount=amount,
        currency=currency,
        metadata={"user_id": user_id},
    )
    return await run_in_threadpool(create, idempotency_key=idempotency_key)


async def confirm_payment_intent(payment_intent_id: str, idempotency_key: Optional[str] = None):
    confirm = partial(stripe.PaymentIntent.confirm, payment_intent_id)
    return await run_in_threadpool(confirm, idempotency_key=idempotency_key)
