import pytest
import stripe

from app.services import stripe_service


class DummyIntent:
    def __init__(
        self,
        intent_id: str,
        status: str,
        client_secret: str = "secret",
        amount: int = 1000,
        currency: str = "usd",
        metadata: dict | None = None,
    ):
        self.id = intent_id
        self.status = status
        self.client_secret = client_secret
        self.amount = amount
        self.currency = currency
        self.metadata = metadata or {}


@pytest.mark.asyncio
async def test_payment_happy_path(client, monkeypatch):
    async def fake_create_payment_intent(user_id, amount, currency="usd", idempotency_key=None):
        return DummyIntent("pi_test", "requires_confirmation", "secret_test", amount, currency, {"user_id": user_id})

    async def fake_confirm_payment_intent(payment_intent_id, idempotency_key=None):
        return DummyIntent(payment_intent_id, "succeeded", "secret_test", 1000, "usd", {"user_id": "user-123"})

    monkeypatch.setattr(stripe_service, "create_payment_intent", fake_create_payment_intent)
    monkeypatch.setattr(stripe_service, "confirm_payment_intent", fake_confirm_payment_intent)

    create_payload = {"user_id": "user-123", "amount": 1000, "currency": "usd", "idempotency_key": "idem-1"}
    resp = await client.post("/api/payments/create-intent", json=create_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["client_secret"] == "secret_test"
    payment_id = data["payment_id"]

    confirm_payload = {"payment_intent_id": "pi_test", "idempotency_key": "idem-1"}
    confirm_resp = await client.post("/api/payments/confirm", json=confirm_payload)
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["status"] == "succeeded"
    assert confirm_data["id"] == payment_id

    # repeat confirm to validate idempotency
    repeat_resp = await client.post("/api/payments/confirm", json=confirm_payload)
    assert repeat_resp.status_code == 200
    assert repeat_resp.json()["id"] == payment_id

    status_resp = await client.get(f"/api/payments/{payment_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "succeeded"


@pytest.mark.asyncio
async def test_payment_stripe_error(client, monkeypatch):
    def raise_card_error(*args, **kwargs):
        raise stripe.error.CardError(
            message="Your card was declined",
            param="",
            code="card_declined",
            http_body=None,
            http_status=None,
            json_body=None,
            headers=None,
        )

    async def fake_create_payment_intent(user_id, amount, currency="usd", idempotency_key=None):
        raise_card_error()

    monkeypatch.setattr(stripe_service, "create_payment_intent", fake_create_payment_intent)

    create_payload = {"user_id": "user-err", "amount": 500, "currency": "usd"}
    resp = await client.post("/api/payments/create-intent", json=create_payload)
    assert resp.status_code == 400
    assert "declined" in resp.json()["detail"]
