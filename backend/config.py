"""
Configuration management using pydantic-settings
Loads configuration from environment variables
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str  # Required - no default for security

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Email Configuration
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_IMAP_HOST: str = ""
    EMAIL_IMAP_PORT: int = 993
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_CC_RECIPIENTS: str = ""  # Optional: comma-separated CC addresses

    # Historical Email Configuration (for backfill)
    HISTORICAL_EMAIL_ADDRESS: str = ""
    HISTORICAL_EMAIL_PASSWORD: str = ""
    HISTORICAL_IMAP_HOST: str = ""
    HISTORICAL_IMAP_PORT: int = 993

    # Backfill Configuration
    BACKFILL_SUBJECT_FILTER: str = "Contact Form:"
    BACKFILL_MAX_EMAILS: int = 1000
    BACKFILL_LOOKBACK_DAYS: int = 365
    BACKFILL_BATCH_SIZE: int = 50

    # AI Configuration - OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Model Selection
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"  # Default model
    OPENROUTER_EXTRACTION_MODEL: str = "anthropic/claude-3.5-sonnet"  # Structured output
    OPENROUTER_RESPONSE_MODEL: str = "anthropic/claude-3.5-sonnet"    # Text generation

    # Model Settings
    LLM_TEMPERATURE_EXTRACTION: float = 0.3  # Low for consistent extraction
    LLM_TEMPERATURE_RESPONSE: float = 0.7    # Higher for natural writing
    LLM_MAX_TOKENS: int = 4000
    LLM_TIMEOUT: int = 60  # seconds

    # Optional: OpenAI for embeddings only
    OPENAI_API_KEY: str = ""

    # CORS - Override via CORS_ORIGINS env var as JSON array
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://frontend:3000",
    ]

    # RAG Configuration
    EMBEDDING_MODEL: str = "claude"  # or "openai"
    EMBEDDING_DIMENSIONS: int = 1536
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 10
    MIN_SIMILARITY_SCORE: float = 0.7

    # Agent Configuration - Product Types
    PRODUCT_TYPES: List[str] = [
        "probiotics", "electrolytes", "protein", "greens", "multivitamin",
        "pre-workout", "post-workout", "sleep", "nootropics", "collagen",
        "omega-3", "amino-acids", "creatine", "weight-management", "detox",
        "energy", "immunity", "joint-health"
    ]

    # Agent Configuration - Certifications
    CERTIFICATIONS: List[str] = [
        "organic", "non-gmo", "vegan", "gluten-free", "gmp", "nsf",
        "kosher", "halal", "third-party-tested"
    ]

    # Agent Configuration - Delivery Formats
    DELIVERY_FORMATS: List[str] = [
        "powder", "capsule", "gummy", "liquid", "tablet", "softgel"
    ]

    # Agent Configuration - Experience Levels
    EXPERIENCE_LEVELS: List[str] = [
        "first-time", "established-brand", "experienced"
    ]

    # Agent Configuration - Timeline Urgency
    TIMELINE_URGENCY_OPTIONS: List[str] = [
        "urgent", "medium-1-3-months", "long-term-6-plus-months", "exploring"
    ]

    # Agent Configuration - Budget Indicators
    BUDGET_INDICATORS: List[str] = [
        "startup", "mid-market", "enterprise"
    ]

    # Response Agent Configuration
    RESPONSE_TONE: str = "professional_b2b"
    MAX_DRAFT_LENGTH: int = 150  # words
    REQUIRE_APPROVAL: bool = True
    MIN_CONFIDENCE_FOR_AUTO_APPROVAL: float = 9.5  # Future use
    INCLUDE_SOURCE_ATTRIBUTION: bool = True

    # Analytics Configuration
    SNAPSHOT_FREQUENCY: str = "daily"
    RETENTION_DAYS: int = 730  # 2 years
    TRENDING_THRESHOLD: float = 0.2  # 20% increase

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    RATE_LIMIT: str = "100/minute"

    # Dashboard Configuration
    ITEMS_PER_PAGE: int = 20
    AUTO_REFRESH_INTERVAL: int = 30  # seconds
    MAX_EXPORT_ROWS: int = 10000

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/system.log"
    LOG_MAX_SIZE_MB: int = 100
    LOG_BACKUP_COUNT: int = 10

    # Monitoring
    HEALTH_CHECK_ENABLED: bool = True
    METRICS_ENABLED: bool = True
    ERROR_REPORTING: bool = False
    SENTRY_DSN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment


# Create global settings instance
settings = Settings()


def validate_settings() -> None:
    """Validate that required settings are properly configured

    Raises:
        ValueError: If required settings are missing or invalid
    """
    errors = []

    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be set and at least 32 characters")

    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL must be set")

    if not settings.OPENROUTER_API_KEY:
        errors.append("OPENROUTER_API_KEY must be set for AI features")

    if settings.ENVIRONMENT == "production":
        if settings.DEBUG:
            errors.append("DEBUG should be False in production")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


def get_settings() -> Settings:
    """Get the global settings instance

    Returns:
        Settings instance
    """
    return settings
