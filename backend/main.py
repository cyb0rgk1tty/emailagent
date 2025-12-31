"""
Supplement Lead Intelligence System - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from database import engine, Base, init_db, close_db
from api import leads, drafts, analytics, knowledge, conversations, backfill, emails, auth
from config import settings, validate_settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Supplement Lead Intelligence System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")

    # Validate configuration
    try:
        validate_settings()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Supplement Lead Intelligence System",
    description="AI-powered lead intelligence for supplement manufacturing with RAG-enhanced responses",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)  # Auth routes at /api/auth
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(backfill.router, tags=["Historical Backfill"])
app.include_router(emails.router, tags=["Emails"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Supplement Lead Intelligence System API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/config")
async def get_config():
    """Get public configuration"""
    return {
        "product_types": settings.PRODUCT_TYPES,
        "certifications": settings.CERTIFICATIONS,
        "delivery_formats": settings.DELIVERY_FORMATS,
        "items_per_page": settings.ITEMS_PER_PAGE
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
