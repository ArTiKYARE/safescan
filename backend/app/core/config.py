"""
SafeScan — Application Configuration
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = Field(default="SafeScan", description="Application name")
    APP_ENV: str = Field(default="development", description="Environment")
    APP_DEBUG: bool = Field(default=True, description="Debug mode")
    APP_SECRET_KEY: str = Field(..., description="Application secret key")
    APP_CORS_ORIGINS: str = Field(
        default="http://localhost:3000",
        description="CORS allowed origins (comma-separated)",
    )

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://safescan:changeme_password@localhost:5432/safescan",
        description="Async PostgreSQL connection string",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow")

    # --- Redis ---
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # --- JWT ---
    JWT_SECRET_KEY: str = Field(..., description="JWT signing secret")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token TTL")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token TTL")

    # --- OAuth2 ---
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None)
    GITHUB_CLIENT_ID: Optional[str] = Field(default=None)
    GITHUB_CLIENT_SECRET: Optional[str] = Field(default=None)

    # --- Email (SMTP) ---
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    SMTP_FROM: str = Field(default="noreply@safescan.io")
    SMTP_TLS: bool = Field(default=True)

    # --- Celery ---
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend",
    )

    # --- Scan Settings ---
    SCAN_MAX_CONCURRENT: int = Field(default=10, description="Max concurrent scans")
    SCAN_MAX_CRAWL_DEPTH: int = Field(default=2, description="Max crawl depth")
    SCAN_MAX_PAGES: int = Field(default=50, description="Max pages per scan")
    SCAN_REQUESTS_PER_SECOND: int = Field(default=20, description="Rate limit per target")
    SCAN_TIMEOUT_SECONDS: int = Field(default=60, description="Per-module timeout")
    SCAN_USER_AGENT: str = Field(
        default="SafeScan/1.0 (+https://safescan.io)",
        description="User-Agent for scan requests",
    )

    # --- Proxies ---
    SCAN_PROXY_ENABLED: bool = Field(default=False)
    SCAN_PROXY_LIST: Optional[str] = Field(default=None)

    # --- Storage (S3/MinIO) ---
    S3_ENDPOINT_URL: str = Field(default="http://localhost:9000")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_BUCKET: str = Field(default="safescan-reports")
    S3_REGION: str = Field(default="us-east-1")

    # --- Compliance ---
    DATA_RETENTION_DAYS: int = Field(default=90, description="Data retention period")
    ENABLE_AUDIT_LOG: bool = Field(default=True, description="Enable audit logging")

    @validator("APP_SECRET_KEY", "JWT_SECRET_KEY")
    @classmethod
    def validate_secret_keys(cls, v: str) -> str:
        if v in ("change-me-to-a-random-string", "change-me-jwt-secret", "dev-secret", "dev-secret-change-me"):
            raise ValueError(
                "Please change the default secret key in production! "
                "Use a strong random value: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    @validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in ("development", "staging", "production"):
            raise ValueError(f"Invalid APP_ENV: {v}. Must be one of: development, staging, production")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()
