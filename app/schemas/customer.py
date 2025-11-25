from datetime import datetime

from pydantic import BaseModel


class CustomerUpsert(BaseModel):
    user_id: str
    stripe_customer_id: str


class CustomerOut(BaseModel):
    user_id: str
    stripe_customer_id: str
    decrypted_token: str
    created_at: datetime | None = None
