# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/main.py
# Purpose: FastAPI application entry point with security middleware
# NOT for: Business logic or database models

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from config import settings
from database import init_db, check_db_connection

# Import routers
from api import import_routes, ai_routes, export_routes, product_routes
from api import listings_routes, keywords_routes, competitors_routes
from api import inventory_routes, analytics_routes, settings_routes
from api import compliance_routes
from api import converter_routes

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

    yield

    # Shutdown
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-API-Key",  # Custom API key header
        "X-Webhook-Secret",  # Webhook authentication
    ],
    expose_headers=["X-Total-Count"],  # For pagination
    max_age=600,  # Cache preflight for 10 minutes
)

# Include routers
app.include_router(import_routes.router)
app.include_router(ai_routes.router)
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


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Marketplace Listing Automation API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env,
        "endpoints": {
            "import": "/api/import",
            "ai": "/api/ai",
            "export": "/api/export",
            "products": "/api/products",
            "listings": "/api/listings",
            "keywords": "/api/keywords",
            "competitors": "/api/competitors",
            "inventory": "/api/inventory",
            "analytics": "/api/analytics",
            "settings": "/api/settings",
            "compliance": "/api/compliance",
            "converter": "/api/converter",
            "docs": "/docs",
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Used by monitoring systems and load balancers.
    """
    db_status = check_db_connection()

    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "environment": settings.app_env,
    }


if __name__ == "__main__":
    import uvicorn

    # Run with: python main.py
    # Or use: uvicorn main:app --reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug,
        log_level="info",
    )
