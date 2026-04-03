from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "LUMIEN – Multi-Tenant Fraud Management SaaS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "lumien_saas_secret_key_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # PostgreSQL Configuration
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/lumien_saas"
    
    # For async PostgreSQL (optional, for future use)
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/lumien_saas"

    class Config:
        env_file = ".env"

settings = Settings()
