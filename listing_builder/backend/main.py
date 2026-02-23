# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/main.py
# Purpose: FastAPI application entry point with security middleware
# NOT for: Business logic or database models

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import structlog

import os

from config import settings

# WHY: Rate limiter prevents API abuse (Groq quota burn, DB flood, scraper overload)
limiter = Limiter(key_func=get_remote_address)
from database import init_db, check_db_connection, SessionLocal

# Import routers
from api import import_routes, export_routes, product_routes
from api import listings_routes, keywords_routes, competitors_routes
from api import inventory_routes, analytics_routes, settings_routes
from api import compliance_routes
from api import converter_routes
from api import optimizer_routes
from api import monitoring_routes
from api import knowledge_routes
from api import keepa_routes
from api import epr_routes
from api import oauth_routes
from api import stripe_routes
from api import news_routes
from api import allegro_routes
from api import allegro_offers_routes
from api import research_routes
from api import auth_routes
from api import admin_routes
from api import alert_settings_routes
from api import ad_copy_routes
from api import listing_score_routes

# Import security middleware
from middleware import APIKeyMiddleware, SecurityHeadersMiddleware, https_redirect_middleware

# Configure logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info("application_starting", env=settings.app_env)

    # Check database connection
    if check_db_connection():
        logger.info("database_connected")
    else:
        logger.error("database_connection_failed")

    # Initialize database tables
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))

    # WHY init here: AlertService needs DB session factory, scheduler needs AlertService
    try:
        from services.alert_service import init_alert_service
        init_alert_service(SessionLocal)
    except Exception as e:
        logger.error("alert_service_init_failed", error=str(e))

    try:
        from services.monitor_scheduler import start_scheduler
        start_scheduler(SessionLocal)
    except Exception as e:
        logger.error("monitor_scheduler_init_failed", error=str(e))

    # NOTE: No pre-warm — Render free tier health check needs fast startup.
    # First user request to /api/news/feed warms the cache (~10s).

    yield

    # Shutdown
    try:
        from services.monitor_scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    logger.info("application_shutting_down")


# Create FastAPI app
# Disable docs in production for security
app = FastAPI(
    title="Marketplace Listing Automation API",
    description="Backend for automated product listing across multiple marketplaces",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_debug else None,  # Hide docs in production
    redoc_url="/redoc" if settings.app_debug else None,  # Hide redoc in production
    openapi_url="/openapi.json" if settings.app_debug else None,  # Hide OpenAPI schema in production
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middleware (order matters - outermost first)

# 1. HTTPS redirect (production only)
app.middleware("http")(https_redirect_middleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. API key authentication
app.add_middleware(APIKeyMiddleware)

# 4. CORS middleware (more restrictive in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-API-Key",  # Custom API key header
        "X-Webhook-Secret",  # Webhook authentication
        "X-License-Key",  # Premium license validation
    ],
    expose_headers=["X-Total-Count"],  # For pagination
    max_age=600,  # Cache preflight for 10 minutes
)

# Include routers
app.include_router(import_routes.router)
app.include_router(export_routes.router)
app.include_router(product_routes.router)
app.include_router(listings_routes.router)
app.include_router(keywords_routes.router)
app.include_router(competitors_routes.router)
app.include_router(inventory_routes.router)
app.include_router(analytics_routes.router)
app.include_router(settings_routes.router)
app.include_router(compliance_routes.router)
app.include_router(converter_routes.router)
app.include_router(optimizer_routes.router)
app.include_router(monitoring_routes.router)
app.include_router(knowledge_routes.router)
app.include_router(keepa_routes.router)
app.include_router(epr_routes.router)
app.include_router(oauth_routes.router)
app.include_router(stripe_routes.router)
app.include_router(news_routes.router)
app.include_router(allegro_routes.router)
app.include_router(allegro_offers_routes.router)
app.include_router(research_routes.router)
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(alert_settings_routes.router)
app.include_router(ad_copy_routes.router)
app.include_router(listing_score_routes.router)


@app.get("/")
async def root():
    """API root endpoint"""
    # WHY: Don't expose environment name or full endpoint map in production —
    # attackers use this to enumerate attack surface
    return {
        "name": "Marketplace Listing Automation API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Used by monitoring systems and load balancers.
    """
    db_status = check_db_connection()

    # WHY: Marketplace config helps diagnose "why isn't X working?" without exposing secrets
    integrations = {
        "groq": bool(settings.groq_api_key),
        "allegro": bool(settings.allegro_client_id),
        "ebay": bool(settings.ebay_app_id),
        "bol": bool(settings.bol_client_id),
        "stripe": bool(settings.stripe_secret_key),
    }

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "integrations": integrations,
    }


if __name__ == "__main__":
    import uvicorn

    # Run with: python main.py
    # Or use: uvicorn main:app --reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),  # WHY: Render injects PORT env var
        reload=settings.app_debug,
        log_level="info",
    )
