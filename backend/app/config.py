"""
Configuration Module
====================
Centralized settings for the entire backend application.

WHY THIS EXISTS:
- Single source of truth for all configuration values
- Reads from environment variables with sensible defaults
- Validates config at startup (fail fast, not at runtime)
- Makes it easy to switch between dev/staging/prod environments

Uses pydantic-settings for automatic env var parsing and validation.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic-settings automatically reads from .env files and environment
    variables. Field names are case-insensitive when matching env vars.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars without error
    )
    
    # ── Application ──────────────────────────────────────────────
    app_name: str = "Multi-Agent Data Analyst"
    app_env: str = "development"  # development | staging | production
    debug: bool = True
    secret_key: str = "change-me-to-a-random-string"
    
    # ── Server ───────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_origins: str = "http://localhost:3000"  # Comma-separated
    
    # ── Database ─────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/multiagent_db"
    
    # ── Groq LLM ─────────────────────────────────────────────────
    # Optional: If not set, agents fall back to rule-based analysis.
    # This dual-mode design lets the app work without any API key.
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    
    # ── Clerk Auth ───────────────────────────────────────────────
    clerk_secret_key: Optional[str] = None
    clerk_webhook_secret: Optional[str] = None
    clerk_jwks_url: Optional[str] = None
    clerk_issuer_url: Optional[str] = None
    
    # ── File Storage ─────────────────────────────────────────────
    storage_backend: str = "local"  # local | s3
    storage_local_path: str = "./storage"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # ── Rate Limiting ────────────────────────────────────────────
    free_tier_monthly_limit: int = 10
    max_file_size_mb: int = 25
    
    # ── Logging ──────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"  # json | console
    
    # ── Derived Properties ───────────────────────────────────────
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB limit to bytes for validation."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    @property
    def llm_enabled(self) -> bool:
        """Check if Groq LLM is configured and available."""
        return bool(self.groq_api_key)
    
    @property
    def storage_path(self) -> Path:
        """Resolved storage directory path."""
        path = Path(self.storage_local_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate_production_secrets(self) -> None:
        """Raise error if running in production with default secrets."""
        if self.is_production and self.secret_key in ("change-me-to-a-random-string", "dev-secret-key-change-in-production"):
            raise ValueError(
                "FATAL: SECRET_KEY is still set to the default value. "
                "Set a strong random SECRET_KEY before running in production."
            )


# ── Singleton ────────────────────────────────────────────────────
# Create a single instance used throughout the app.
# Import this in other modules: `from app.config import settings`
settings = Settings()
