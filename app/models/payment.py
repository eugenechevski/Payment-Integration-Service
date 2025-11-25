import sqlalchemy as sa
from sqlalchemy.sql import func

from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.String, nullable=False, index=True)
    amount = sa.Column(sa.Integer, nullable=False)  # cents
    currency = sa.Column(sa.String(10), nullable=False, default="usd")
    status = sa.Column(sa.String(50), nullable=False)
    stripe_payment_id = sa.Column(sa.String, nullable=False, unique=True)
    client_secret = sa.Column(sa.String, nullable=True)
    idempotency_key = sa.Column(sa.String, nullable=True, unique=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
    updated_at = sa.Column(
        sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
