from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field(
        "sqlite+aiosqlite:///./dev.db",
        alias="DATABASE_URL",
        description="Database connection string",
    )
    stripe_api_key: str = Field(
        "sk_test_placeholder",
        alias="STRIPE_API_KEY",
        description="Stripe test secret key",
    )
    encryption_key: str = Field(
        "gR2S4YVd_FqjUKPTy3lNMHvrYb2n0V5xsV6pQNwbabE=",
        alias="ENCRYPTION_KEY",
        description="Fernet base64 key",
    )
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()  # loads environment at import time
