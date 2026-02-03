# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/config.py
# Purpose: Application configuration and environment variables
# NOT for: Business logic or database models

from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator
import os
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for type validation and .env file support.
    """

    # App
    app_env: str = "development"
    app_debug: bool = True
    api_secret_key: str  # REQUIRED - no default value
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Database - Supabase PostgreSQL
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    database_url: str

    # Redis Queue
    redis_url: str = "redis://localhost:6379/0"

    # AI/LLM - Groq (PRIMARY, NOT OpenAI)
    groq_api_key: str

    # Marketplace APIs
    amazon_refresh_token: str = ""
    amazon_client_id: str = ""
    amazon_client_secret: str = ""
    amazon_region: str = "eu-west-1"

    ebay_app_id: str = ""
    ebay_cert_id: str = ""
    ebay_dev_id: str = ""
    ebay_user_token: str = ""

    kaufland_client_key: str = ""
    kaufland_secret_key: str = ""

    # Webhook Security
    webhook_secret: str  # REQUIRED - no default value

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # WHY: Don't crash on unknown env vars (e.g. linkedin_li_at)

    @field_validator("api_secret_key", "webhook_secret")
    @classmethod
    def validate_secrets(cls, v: str, info) -> str:
        """
        Validate that secrets are not weak/default values.

        Why: Prevents accidentally deploying with insecure defaults.
        """
        weak_secrets = [
            "change-me",
            "change-me-in-production",
            "secret",
            "password",
            "test",
            "12345",
        ]

        if v.lower() in weak_secrets:
            raise ValueError(
                f"{info.field_name} contains a weak/default value. "
                f"Generate a secure secret with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        if len(v) < 16:
            raise ValueError(f"{info.field_name} must be at least 16 characters long")

        return v

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """Validate environment is valid"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"app_env must be one of: {allowed}")
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"


# Global settings instance
# Will raise ValidationError if required fields missing or secrets are weak
settings = Settings()
