from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.logging import logger  # ensure logging configured on import

app = FastAPI(title="Payment Integration Service")


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("Payment Integration Service started")
