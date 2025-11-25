import sqlalchemy as sa
from sqlalchemy.sql import func

from app.models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.String, nullable=False, unique=True, index=True)
    stripe_customer_id = sa.Column(sa.String, nullable=False)
    encrypted_token = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
