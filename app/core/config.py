"""Application configuration."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # 1. OPTIONAL DEFAULTS (Safe to leave here)
    APP_NAME: str = "AIOA - Personal Finance Manager"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str | None = None  # comma-separated list, e.g. "http://localhost:5173,https://your-ui.com"

    # 2. REQUIRED FROM .ENV (No defaults provided!)
    # If these are missing from your .env file, the app will crash on startup
    DATABASE_URL: str
    SECRET_KEY: str

    # 3. SUPABASE CONFIGURATION (Optional)
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    
    # Extra DB config fields (optional)
    db_pass: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    user: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
