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
    app_debug: bool = False  # SECURITY: Default off — docs hidden unless explicitly enabled
    api_secret_key: str  # REQUIRED - no default value
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Database - Supabase PostgreSQL
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    database_url: str

    # AI/LLM - Groq (PRIMARY, NOT OpenAI)
    groq_model: str = "llama-3.3-70b-versatile"  # WHY: Configurable via env — test new models without code change
    groq_api_key: str
    groq_api_key_2: str = ""  # WHY: Backup keys for rotation on 429 rate limits
    groq_api_key_3: str = ""
    groq_api_key_4: str = ""
    groq_api_key_5: str = ""
    groq_api_key_6: str = ""
    groq_api_key_7: str = ""  # WHY: 7th key for extended rotation pool
    groq_api_key_8: str = ""  # WHY: 8th key for extended rotation pool

    # Marketplace APIs
    amazon_refresh_token: str = ""
    amazon_client_id: str = ""
    amazon_client_secret: str = ""
    amazon_region: str = "eu-west-1"

    ebay_app_id: str = ""  # WHY: eBay OAuth app credentials (from Mateusz)
    ebay_cert_id: str = ""
    ebay_dev_id: str = ""
    ebay_ru_name: str = ""  # WHY: eBay Redirect URL Name — generated in eBay Developer portal

    allegro_client_id: str = ""  # WHY: Allegro OAuth app credentials (from Mateusz)
    allegro_client_secret: str = ""

    bol_client_id: str = ""  # WHY: BOL.com Retailer API credentials (Client Credentials grant)
    bol_client_secret: str = ""

    kaufland_client_key: str = ""
    kaufland_secret_key: str = ""

    # RAG Search Mode + Cloudflare Workers AI embeddings (free)
    rag_mode: str = "hybrid"  # WHY: "lexical" | "hybrid" | "semantic" — embeddings ready, hybrid active
    cf_account_id: str = ""  # WHY: Cloudflare account for Workers AI embeddings
    cf_auth_email: str = ""  # Cloudflare auth email
    cf_api_key: str = ""  # Cloudflare Global API Key

    # Scraping
    scrape_do_token: str = ""  # Scrape.do API token (recommended for Allegro)
    scraper_proxy_url: str = ""  # Fallback: raw residential proxy URL

    # n8n Integration (optional — empty = skip n8n, use direct Groq only)
    n8n_webhook_url: str = ""
    n8n_webhook_secret: str = ""

    # Stripe (license key monetization — monthly subscription)
    stripe_secret_key: str = ""  # WHY: Empty = Stripe disabled (dev mode)
    stripe_price_monthly: str = ""  # WHY: 49 PLN/month subscription
    stripe_webhook_secret: str = ""  # WHY: Stripe signs webhooks with this

    # Supabase Auth (JWT verification)
    supabase_jwt_secret: str = ""  # WHY: Empty = JWT auth disabled (backward compat)

    # Admin access control
    admin_emails: str = ""  # WHY: Comma-separated admin emails — checked by require_admin()

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
    def admin_emails_list(self) -> List[str]:
        """Parse admin emails from comma-separated env var, lowercased."""
        if not self.admin_emails:
            return []
        return [e.strip().lower() for e in self.admin_emails.split(",") if e.strip()]

    @property
    def groq_api_keys(self) -> List[str]:
        """All available Groq API keys for rotation."""
        keys = [self.groq_api_key]
        for attr in ("groq_api_key_2", "groq_api_key_3", "groq_api_key_4",
                      "groq_api_key_5", "groq_api_key_6", "groq_api_key_7",
                      "groq_api_key_8"):
            val = getattr(self, attr, "")
            if val:
                keys.append(val)
        return keys

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"


# Global settings instance
# Will raise ValidationError if required fields missing or secrets are weak
settings = Settings()
