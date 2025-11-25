from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_value, encrypt_value
from app.core.logging import logger
from app.db.session import get_session
from app.models.customer import Customer
from app.schemas.customer import CustomerOut, CustomerUpsert

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut)
async def upsert_customer(payload: CustomerUpsert, db: AsyncSession = Depends(get_session)):
    encrypted = encrypt_value(payload.stripe_customer_id)
    result = await db.execute(select(Customer).where(Customer.user_id == payload.user_id))
    customer = result.scalar_one_or_none()

    if customer:
        logger.info("Updating customer", extra={"user_id": payload.user_id})
        customer.stripe_customer_id = payload.stripe_customer_id
        customer.encrypted_token = encrypted
    else:
        logger.info("Creating customer", extra={"user_id": payload.user_id})
        customer = Customer(
            user_id=payload.user_id,
            stripe_customer_id=payload.stripe_customer_id,
            encrypted_token=encrypted,
        )
        db.add(customer)

    await db.commit()
    await db.refresh(customer)
    return CustomerOut(
        user_id=customer.user_id,
        stripe_customer_id=customer.stripe_customer_id,
        decrypted_token=payload.stripe_customer_id,
        created_at=customer.created_at,
    )


@router.get("/{user_id}", response_model=CustomerOut)
async def get_customer(user_id: str, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Customer).where(Customer.user_id == user_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    decrypted = decrypt_value(customer.encrypted_token)
    return CustomerOut(
        user_id=customer.user_id,
        stripe_customer_id=customer.stripe_customer_id,
        decrypted_token=decrypted,
        created_at=customer.created_at,
    )
