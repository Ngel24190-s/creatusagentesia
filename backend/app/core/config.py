from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "NosVers API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nosvers:changeme@db:5432/nosvers"

    # Auth
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # WooCommerce
    WOOCOMMERCE_URL: str = ""
    WOOCOMMERCE_KEY: str = ""
    WOOCOMMERCE_SECRET: str = ""

    # QR / Traceability
    PUBLIC_TRACE_URL: str = "https://nosvers.com/trace"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
