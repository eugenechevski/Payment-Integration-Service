# Payment Integration Service

FastAPI + PostgreSQL service that mirrors the resume line: “Payment Integration Service | Python, FastAPI, PostgreSQL, Stripe API – Developed secure transaction endpoints supporting card verification and error recovery. Implemented encryption for stored tokens and tested API endpoints for concurrency handling. Collaborated with frontend teams to synchronize session and payment flow in live environments.”

## Tech Stack
- FastAPI, Uvicorn
- PostgreSQL (async SQLAlchemy + asyncpg)
- Stripe (test mode)
- Cryptography (Fernet encryption for stored tokens)
- Docker / docker compose
- Pytest + httpx + pytest-asyncio

## Project Structure
```
app/
  api/           # Routers (payments, customers)
  core/          # Config, logging, crypto utils
  db/            # Session/engine
  models/        # SQLAlchemy models
  schemas/       # Pydantic schemas
  services/      # Stripe integration
  main.py        # FastAPI entrypoint
sql/init.sql     # SQL to bootstrap tables if not using Alembic
tests/           # Health + payment flow tests (Stripe mocked)
```

## Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env  # update DATABASE_URL, STRIPE_API_KEY, ENCRYPTION_KEY
# generate a Fernet key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Run the app (dev):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Health check: `GET http://localhost:8000/health`

## Database
- Default env expects Postgres. For quick starts without Alembic, run `sql/init.sql`.
- `DATABASE_URL` example: `postgresql+asyncpg://user:password@localhost:5432/payment_db`

## Stripe (Test Mode)
- Set `STRIPE_API_KEY` to a Stripe test secret key (or mock in tests).
- Endpoints:
  - `POST /api/payments/create-intent` → returns `payment_id` + `client_secret`
  - `POST /api/payments/confirm` → idempotent confirm with `idempotency_key`
  - `GET  /api/payments/{payment_id}` → stored status
  - `POST /api/customers` and `GET /api/customers/{user_id}` → store/retrieve encrypted Stripe customer id

Frontend flow: call create-intent, confirm card on frontend with `client_secret`, then backend confirm (with `idempotency_key`), and poll status.

## Error Recovery & Concurrency
- `idempotency_key` on creation/confirmation prevents double charges on retries.
- DB writes + Stripe calls are logged for traceability.
- Unique idempotency keys + DB lookups ensure safe repeated calls even under concurrency.
- Quick concurrency probe (example):
```python
import asyncio, httpx

async def hit():
    payload = {"payment_intent_id": "pi_test", "idempotency_key": "idem-123"}
    async with httpx.AsyncClient() as client:
        return await client.post("http://localhost:8000/api/payments/confirm", json=payload)

async def main():
    results = await asyncio.gather(*[hit() for _ in range(5)])
    print([r.json() for r in results])

asyncio.run(main())
```

## Encryption
- `cryptography` Fernet key from `ENCRYPTION_KEY` encrypts stored tokens (e.g., Stripe customer id). Raw card data is never stored; Stripe handles PCI scope.

## Docker
```bash
docker compose up --build
# app on :8000, Postgres on :5432
```
Running migrations inside the container (once Alembic is configured):
```bash
docker compose run --rm payment-service alembic upgrade head
```

## Tests
```bash
pytest
```
- Health check test runs in-memory.
- Payment flow tests mock Stripe to demonstrate happy/error paths and idempotency behavior.

## Git Commands (example)
```bash
git init
git add .
git commit -m "feat: initial payment service scaffold"
git remote add origin git@github.com:<username>/payment-integration-service.git
git push -u origin main
```

Suggested GitHub description: “FastAPI + PostgreSQL payment integration with Stripe test mode, encrypted customer tokens, and concurrency-safe endpoints.”
