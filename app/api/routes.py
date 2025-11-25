from fastapi import APIRouter

from app.api import customers, payments

router = APIRouter()
router.include_router(payments.router)
router.include_router(customers.router)
