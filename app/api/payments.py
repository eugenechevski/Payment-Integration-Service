from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

from app.core.logging import logger
from app.db.session import get_session
from app.models.payment import Payment
from app.schemas.payment import (
    ConfirmPaymentRequest,
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentStatusResponse,
)
from app.services import stripe_service

router = APIRouter(prefix="/payments", tags=["payments"])


def _to_response(payment: Payment) -> PaymentStatusResponse:
    return PaymentStatusResponse(
        id=payment.id,
    user_id=payment.user_id,
    amount=payment.amount,
    currency=payment.currency,
    status=payment.status,
    client_secret=payment.client_secret,
    stripe_payment_id=payment.stripe_payment_id,
    created_at=payment.created_at,
    updated_at=payment.updated_at,
    )


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_intent(
    payload: CreatePaymentIntentRequest, db: AsyncSession = Depends(get_session)
):
    logger.info(
        "Creating payment intent",
        extra={"user_id": payload.user_id, "amount": payload.amount, "currency": payload.currency},
    )

    if payload.idempotency_key:
        existing = await db.execute(
            select(Payment).where(Payment.idempotency_key == payload.idempotency_key)
        )
        existing_payment = existing.scalar_one_or_none()
        if existing_payment:
            return PaymentIntentResponse(
                payment_id=existing_payment.id,
                client_secret=existing_payment.client_secret or "",
                status=existing_payment.status,
            )

    try:
        intent = await stripe_service.create_payment_intent(
            user_id=payload.user_id,
            amount=payload.amount,
            currency=payload.currency,
            idempotency_key=payload.idempotency_key,
        )
    except stripe.error.StripeError as exc:
        logger.exception("Stripe create payment intent failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message or str(exc)
        )
    except Exception as exc:  # pragma: no cover - unexpected path
        logger.exception("Unexpected error creating payment intent")
        raise HTTPException(status_code=500, detail="Failed to create payment intent") from exc

    payment = Payment(
        user_id=payload.user_id,
        amount=payload.amount,
        currency=payload.currency,
        status=intent.status,
        stripe_payment_id=intent.id,
        client_secret=intent.client_secret,
        idempotency_key=payload.idempotency_key,
    )
    db.add(payment)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.info("Intent create detected duplicate idempotency key; returning existing row")
        existing = await db.execute(
            select(Payment).where(Payment.idempotency_key == payload.idempotency_key)
        )
        payment = existing.scalar_one_or_none()
        if payment:
            return PaymentIntentResponse(
                payment_id=payment.id, client_secret=intent.client_secret, status=payment.status
            )
        raise HTTPException(status_code=409, detail="Duplicate payment request")
    await db.refresh(payment)

    return PaymentIntentResponse(
        payment_id=payment.id, client_secret=intent.client_secret, status=intent.status
    )


@router.post("/confirm", response_model=PaymentStatusResponse)
async def confirm_payment(
    payload: ConfirmPaymentRequest, db: AsyncSession = Depends(get_session)
):
    logger.info(
        "Confirming payment intent",
        extra={"intent_id": payload.payment_intent_id, "idempotency_key": payload.idempotency_key},
    )

    payment = None
    if payload.idempotency_key:
        existing = await db.execute(
            select(Payment).where(Payment.idempotency_key == payload.idempotency_key)
        )
        payment = existing.scalar_one_or_none()
        if payment:
            return _to_response(payment)

    if not payment:
        existing_by_intent = await db.execute(
            select(Payment).where(Payment.stripe_payment_id == payload.payment_intent_id)
        )
        payment = existing_by_intent.scalar_one_or_none()

    try:
        intent = await stripe_service.confirm_payment_intent(
            payment_intent_id=payload.payment_intent_id, idempotency_key=payload.idempotency_key
        )
    except stripe.error.StripeError as exc:
        logger.exception("Stripe confirm failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.user_message or str(exc)
        )
    except Exception as exc:  # pragma: no cover - unexpected path
        logger.exception("Unexpected error confirming payment")
        raise HTTPException(status_code=500, detail="Failed to confirm payment") from exc

    if payment:
        payment.status = intent.status
        payment.idempotency_key = payment.idempotency_key or payload.idempotency_key
        payment.amount = payment.amount or intent.amount
        payment.currency = payment.currency or intent.currency
        payment.client_secret = payment.client_secret or getattr(intent, "client_secret", None)
        await db.commit()
        await db.refresh(payment)
        return _to_response(payment)

    # Handle race where confirm arrives before record exists
    payment = Payment(
        user_id=intent.metadata.get("user_id", ""),
        amount=intent.amount,
        currency=intent.currency,
        status=intent.status,
        stripe_payment_id=intent.id,
        client_secret=getattr(intent, "client_secret", None),
        idempotency_key=payload.idempotency_key,
    )
    db.add(payment)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.info("Confirm encountered existing idempotency key, returning stored payment")
        existing = await db.execute(
            select(Payment).where(Payment.idempotency_key == payload.idempotency_key)
        )
        stored = existing.scalar_one_or_none()
        if stored:
            return _to_response(stored)
        raise HTTPException(status_code=409, detail="Duplicate payment confirmation")

    await db.refresh(payment)
    return _to_response(payment)


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return _to_response(payment)
