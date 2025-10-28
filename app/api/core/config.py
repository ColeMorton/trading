"""
API Configuration Settings.

This module provides configuration management for the Trading CLI API
using pydantic-settings for environment-based configuration.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings with environment variable support."""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Trading CLI API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "FastAPI wrapper for trading-cli with async job queue and SSE streaming"
    )

    # Security
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_MIN_LENGTH: int = 32
    API_KEY_SECRET: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret for hashing API keys",
    )

    # Redis/ARQ Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )
    ARQ_QUEUE_NAME: str = "trading_jobs"
    REDIS_MAX_CONNECTIONS: int = 50

    # Job Configuration
    JOB_TIMEOUT: int = 3600  # 1 hour max
    JOB_CLEANUP_DAYS: int = 7
    MAX_CONCURRENT_JOBS: int = 10
    JOB_RETRY_ATTEMPTS: int = 3

    # Rate Limiting
    RATE_LIMIT_DEFAULT: int = 60  # requests per minute
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_BURST: int = 10  # allow burst above rate limit

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://trading_user:trading_password@localhost:5432/trading_db",
        description="PostgreSQL connection URL",
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Application Settings
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    LOG_LEVEL: str = "INFO"

    # File Storage
    RESULT_STORAGE_PATH: str = Field(
        default="./data/api_results", description="Path for storing job results"
    )
    MAX_RESULT_SIZE_MB: int = 100

    # SSE Configuration
    SSE_POLL_INTERVAL: float = 0.5  # seconds
    SSE_MAX_DURATION: int = 3600  # 1 hour max connection

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_local_development(self) -> bool:
        """Strict check for local development environment."""
        return (
            self.ENVIRONMENT == "development" 
            and self.DEBUG is True
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # Ignore extra environment variables not in this model
    }


# Global settings instance
settings = APISettings()
