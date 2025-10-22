# Supplement Lead Intelligence System - Implementation Task List

**Project:** NutriCraft Labs Email Agent
**Version:** 2.0
**Reference:** See PRD.md for detailed requirements
**Target:** AI Coding Agent Implementation
**Timeline:** 5 Weeks (200 hours)

---

## Important Notes for AI Agent

### Port Assignments (Conflict-Free)
- **FastAPI Backend:** 8001 (external) → 8000 (internal)
- **React Frontend:** 3001 (external) → 3000 (internal)
- **PostgreSQL:** 5434 (external) → 5432 (internal)
- **Redis:** 6380 (external) → 6379 (internal)
- **pgAdmin (optional):** 5050

### Project Structure
```
/var/www/emailagent/
├── backend/
├── frontend/
├── knowledge/
├── planning/
├── scripts/
├── tests/
├── logs/
├── docker-compose.yml
├── .env
└── .env.example
```

---

# PHASE 1: Foundation & Infrastructure (Week 1)

## Task 1.1: Project Directory Structure Setup

**Priority:** Critical
**Estimated Time:** 30 minutes
**Dependencies:** None

### Actions:
1. Create the following directory structure:
```bash
/var/www/emailagent/
├── backend/
│   ├── agents/
│   ├── rag/
│   ├── services/
│   ├── api/
│   ├── models/
│   └── tasks/
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/
├── knowledge/
│   ├── products/
│   ├── pricing/
│   ├── capabilities/
│   ├── certifications/
│   └── faq/
├── scripts/
├── tests/
├── logs/
└── alembic/
    └── versions/
```

2. Create placeholder README.md files in each major directory

### Acceptance Criteria:
- [ ] All directories exist
- [ ] Directory structure matches PRD Section 5.1
- [ ] README.md files exist in backend/, frontend/, knowledge/

---

## Task 1.2: Environment Configuration Files

**Priority:** Critical
**Estimated Time:** 1 hour
**Dependencies:** Task 1.1

### Actions:

1. **Create `.env.example`** at `/var/www/emailagent/.env.example`:
```bash
# Database Configuration
DB_USER=emailagent_user
DB_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
DB_HOST=postgres
DB_PORT=5432
DB_NAME=supplement_leads_db

# Email Configuration (Email MCP Server)
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=contact@nutricraftlabs.com
EMAIL_PASSWORD=YOUR_EMAIL_APP_PASSWORD

# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here

# Application
SECRET_KEY=your-secret-key-for-jwt-tokens
ENVIRONMENT=development
DEBUG=true

# Redis
REDIS_URL=redis://redis:6379

# Optional: Monitoring
SENTRY_DSN=
```

2. **Create `.env`** by copying `.env.example` and adding real credentials (DO NOT COMMIT)

3. **Create `.gitignore`** at `/var/www/emailagent/.gitignore`:
```
.env
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/
node_modules/
.DS_Store
logs/*.log
*.sqlite3
.pytest_cache/
.coverage
htmlcov/
.vscode/
.idea/
```

### Acceptance Criteria:
- [ ] `.env.example` exists with all required variables
- [ ] `.env` exists (with placeholder values initially)
- [ ] `.gitignore` properly excludes sensitive files
- [ ] `.env` is NOT tracked by git

---

## Task 1.3: Docker Compose Configuration

**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Task 1.2

### Actions:

**Create `docker-compose.yml`** at `/var/www/emailagent/docker-compose.yml`:

```yaml
name: emailagent

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: emailagent_postgres
    restart: unless-stopped
    ports:
      - "5434:5432"  # External port 5434 to avoid conflicts
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "-E UTF8"
    volumes:
      - emailagent_postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - emailagent_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: emailagent_redis
    restart: unless-stopped
    ports:
      - "6380:6379"  # External port 6380 to avoid conflicts
    volumes:
      - emailagent_redis_data:/data
    networks:
      - emailagent_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: emailagent_backend
    restart: unless-stopped
    ports:
      - "8001:8000"  # External port 8001 to avoid conflicts
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      EMAIL_ADDRESS: ${EMAIL_ADDRESS}
      EMAIL_PASSWORD: ${EMAIL_PASSWORD}
      EMAIL_IMAP_HOST: ${EMAIL_IMAP_HOST}
      EMAIL_IMAP_PORT: ${EMAIL_IMAP_PORT}
      EMAIL_SMTP_HOST: ${EMAIL_SMTP_HOST}
      EMAIL_SMTP_PORT: ${EMAIL_SMTP_PORT}
      ENVIRONMENT: ${ENVIRONMENT}
      DEBUG: ${DEBUG}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./knowledge:/app/knowledge
      - ./logs:/app/logs
    networks:
      - emailagent_network
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: emailagent_celery_worker
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      REDIS_URL: redis://redis:6379
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      EMAIL_ADDRESS: ${EMAIL_ADDRESS}
      EMAIL_PASSWORD: ${EMAIL_PASSWORD}
      EMAIL_IMAP_HOST: ${EMAIL_IMAP_HOST}
      EMAIL_SMTP_HOST: ${EMAIL_SMTP_HOST}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./knowledge:/app/knowledge
      - ./logs:/app/logs
    networks:
      - emailagent_network
    command: celery -A tasks.celery_app worker --loglevel=info

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: emailagent_celery_beat
    restart: unless-stopped
    environment:
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    networks:
      - emailagent_network
    command: celery -A tasks.celery_app beat --loglevel=info

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: emailagent_frontend
    restart: unless-stopped
    ports:
      - "3001:3000"  # External port 3001 to avoid conflicts
    environment:
      VITE_API_URL: http://localhost:8001
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - emailagent_network

  # Optional: pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: emailagent_pgadmin
    restart: unless-stopped
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@nutricraftlabs.com
      PGADMIN_DEFAULT_PASSWORD: admin
    volumes:
      - emailagent_pgadmin_data:/var/lib/pgadmin
    networks:
      - emailagent_network
    profiles:
      - tools  # Only start with: docker-compose --profile tools up

networks:
  emailagent_network:
    driver: bridge
    name: emailagent_network

volumes:
  emailagent_postgres_data:
    name: emailagent_postgres_data
  emailagent_redis_data:
    name: emailagent_redis_data
  emailagent_pgadmin_data:
    name: emailagent_pgadmin_data
```

### Acceptance Criteria:
- [ ] docker-compose.yml exists
- [ ] All ports are conflict-free (8001, 3001, 5434, 6380)
- [ ] Health checks configured for postgres and redis
- [ ] Volume names prefixed with `emailagent_`
- [ ] Network named `emailagent_network`
- [ ] pgAdmin optional with `--profile tools`

---

## Task 1.4: Backend Dockerfile

**Priority:** Critical
**Estimated Time:** 1 hour
**Dependencies:** Task 1.3

### Actions:

**Create `backend/Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Acceptance Criteria:
- [ ] Dockerfile exists at `/var/www/emailagent/backend/Dockerfile`
- [ ] Uses Python 3.11-slim
- [ ] Installs PostgreSQL client libraries
- [ ] Creates logs directory
- [ ] Exposes port 8000

---

## Task 1.5: Backend Requirements.txt

**Priority:** Critical
**Estimated Time:** 30 minutes
**Dependencies:** Task 1.4

### Actions:

**Create `backend/requirements.txt`**:
```txt
# Web Framework
fastapi==0.119.0
uvicorn[standard]==0.38.0
python-multipart==0.0.9

# Database
sqlalchemy==2.0.23
alembic==1.17.0
asyncpg==0.30.0
psycopg2-binary==2.9.9

# Vector Database
pgvector==0.2.4

# Redis & Background Jobs
redis==6.4.0
celery[redis]==5.3.4

# AI & Embeddings
anthropic==0.18.1
openai==1.12.0

# Email (will use MCP server)
python-dotenv==1.1.1

# Data Validation
pydantic==2.5.3
pydantic-settings==2.1.0
email-validator==2.1.0

# Document Processing for RAG
PyPDF2==3.0.1
python-docx==1.1.0
python-pptx==0.6.23
markdown==3.5.2

# Text Processing
tiktoken==0.5.2

# HTTP Client
httpx==0.28.1
aiohttp==3.13.1

# Utilities
python-dateutil==2.8.2
pytz==2024.1

# Testing
pytest==8.4.2
pytest-asyncio==1.2.0
pytest-cov==7.0.0

# Code Quality
black==25.9.0
ruff==0.14.1
mypy==1.18.2

# Logging
structlog==25.4.0
```

### Acceptance Criteria:
- [ ] requirements.txt exists
- [ ] All versions pinned
- [ ] Compatible with existing server packages
- [ ] Includes all dependencies from PRD Section 2.2

---

## Task 1.6: PostgreSQL Database Schema

**Priority:** Critical
**Estimated Time:** 3 hours
**Dependencies:** Task 1.3

### Actions:

**Create `scripts/init-db.sql`**:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,

    -- Sender information
    sender_email TEXT NOT NULL,
    sender_name TEXT,
    company_name TEXT,
    phone TEXT,

    -- Email content
    subject TEXT,
    body TEXT,
    received_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,

    -- Supplement-specific data (arrays)
    product_type TEXT[],
    specific_ingredients TEXT[],
    delivery_format TEXT[],
    certifications_requested TEXT[],

    -- Business intelligence
    estimated_quantity TEXT,
    timeline_urgency TEXT,
    budget_indicator TEXT,
    experience_level TEXT,
    distribution_channel TEXT[],
    has_existing_brand BOOLEAN,

    -- Lead scoring
    lead_quality_score INTEGER CHECK (lead_quality_score BETWEEN 1 AND 10),
    response_priority TEXT CHECK (response_priority IN ('critical', 'high', 'medium', 'low')),

    -- Additional metadata
    specific_questions TEXT[],
    geographic_region TEXT,
    extraction_confidence FLOAT,
    internal_notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for leads
CREATE INDEX idx_leads_received ON leads(received_at DESC);
CREATE INDEX idx_leads_product_type ON leads USING GIN(product_type);
CREATE INDEX idx_leads_quality ON leads(lead_quality_score DESC);
CREATE INDEX idx_leads_priority ON leads(response_priority);
CREATE INDEX idx_leads_email ON leads(sender_email);
CREATE INDEX idx_leads_processed ON leads(processed_at) WHERE processed_at IS NOT NULL;

-- Create drafts table
CREATE TABLE IF NOT EXISTS drafts (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Draft content
    subject_line TEXT NOT NULL,
    draft_content TEXT NOT NULL,

    -- Status and metadata
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'sent', 'edited')),
    response_type TEXT,
    confidence_score FLOAT,
    flags TEXT[],
    rag_sources TEXT[],

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP,

    -- Approval workflow
    reviewed_by TEXT,
    approval_feedback TEXT,
    edit_summary TEXT,

    -- Learning data
    customer_replied BOOLEAN,
    customer_sentiment TEXT CHECK (customer_sentiment IN ('positive', 'neutral', 'negative'))
);

-- Create indexes for drafts
CREATE INDEX idx_drafts_status ON drafts(status);
CREATE INDEX idx_drafts_pending ON drafts(status) WHERE status = 'pending';
CREATE INDEX idx_drafts_lead ON drafts(lead_id);
CREATE INDEX idx_drafts_created ON drafts(created_at DESC);

-- Create document_embeddings table for RAG
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,

    -- Document identification
    document_name TEXT NOT NULL,
    document_type TEXT NOT NULL CHECK (document_type IN ('product_catalog', 'pricing', 'certification', 'capability', 'faq')),
    section_title TEXT,

    -- Content and embeddings
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding vector(1536),

    -- Metadata
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for document_embeddings
CREATE INDEX idx_embeddings_vector ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_embeddings_type ON document_embeddings(document_type);
CREATE INDEX idx_embeddings_active ON document_embeddings(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_embeddings_document ON document_embeddings(document_name, version);

-- Create product_type_trends table
CREATE TABLE IF NOT EXISTS product_type_trends (
    id SERIAL PRIMARY KEY,
    product_type TEXT NOT NULL,
    date DATE NOT NULL,
    mention_count INTEGER DEFAULT 1,
    lead_count INTEGER DEFAULT 1,
    avg_quality_score FLOAT,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(product_type, date)
);

-- Create indexes for product_type_trends
CREATE INDEX idx_trends_date ON product_type_trends(date DESC);
CREATE INDEX idx_trends_product ON product_type_trends(product_type);

-- Create analytics_snapshots table
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    period_type TEXT NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly')),
    metrics JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(snapshot_date, period_type)
);

-- Create index for analytics_snapshots
CREATE INDEX idx_snapshots_date ON analytics_snapshots(snapshot_date DESC);
CREATE INDEX idx_snapshots_period ON analytics_snapshots(period_type);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for leads table
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for document_embeddings table
CREATE TRIGGER update_embeddings_updated_at
    BEFORE UPDATE ON document_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Acceptance Criteria:
- [ ] init-db.sql exists at `/var/www/emailagent/scripts/init-db.sql`
- [ ] pgvector extension enabled
- [ ] All 5 tables created (leads, drafts, document_embeddings, product_type_trends, analytics_snapshots)
- [ ] All indexes created as per PRD Section 5.2
- [ ] Triggers for updated_at timestamps
- [ ] Foreign key constraints properly set

---

## Task 1.7: Alembic Database Migrations Setup

**Priority:** High
**Estimated Time:** 1 hour
**Dependencies:** Task 1.6

### Actions:

1. **Create `backend/alembic.ini`**:
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://%(DB_USER)s:%(DB_PASSWORD)s@localhost:5434/%(DB_NAME)s

[alembic:exclude]
tables = spatial_ref_sys

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

2. **Initialize Alembic** (will be done when backend starts):
```bash
cd backend
alembic init alembic
```

3. **Create initial migration** in `backend/alembic/versions/001_initial_schema.py`:
```python
"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-10-20

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # The schema is already created by init-db.sql
    # This migration serves as a record
    pass


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('analytics_snapshots')
    op.drop_table('product_type_trends')
    op.drop_table('document_embeddings')
    op.drop_table('drafts')
    op.drop_table('leads')
    op.execute('DROP EXTENSION IF EXISTS vector')
```

### Acceptance Criteria:
- [ ] alembic.ini configured
- [ ] Alembic directory structure exists
- [ ] Initial migration file created
- [ ] Database URL uses port 5434 for external access

---

## Task 1.8: Backend Main Application Setup

**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Task 1.5, 1.6

### Actions:

**Create `backend/main.py`**:
```python
"""
Supplement Lead Intelligence System - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from database import engine, Base
from api import leads, drafts, analytics, knowledge
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Supplement Lead Intelligence System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")

    # Create tables (if not already created by init-db.sql)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await engine.dispose()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Supplement Lead Intelligence System",
    description="AI-powered lead intelligence for supplement manufacturing",
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
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge Base"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Supplement Lead Intelligence System API",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### Acceptance Criteria:
- [ ] main.py exists
- [ ] FastAPI application configured
- [ ] CORS middleware enabled
- [ ] Health check endpoint works
- [ ] API documentation at /api/docs

---

## Task 1.9: Backend Configuration Module

**Priority:** Critical
**Estimated Time:** 1 hour
**Dependencies:** Task 1.2

### Actions:

**Create `backend/config.py`**:
```python
"""
Configuration management using pydantic-settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # Email Configuration
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str
    EMAIL_IMAP_HOST: str
    EMAIL_IMAP_PORT: int = 993
    EMAIL_SMTP_HOST: str
    EMAIL_SMTP_PORT: int = 587

    # API Keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://nutricraftlabs.com"
    ]

    # RAG Configuration
    EMBEDDING_MODEL: str = "claude"  # or "openai"
    EMBEDDING_DIMENSIONS: int = 1536
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 10
    MIN_SIMILARITY_SCORE: float = 0.7

    # Agent Configuration
    PRODUCT_TYPES: List[str] = [
        "probiotics", "electrolytes", "protein", "greens", "multivitamin",
        "pre-workout", "post-workout", "sleep", "nootropics", "collagen",
        "omega-3", "amino-acids", "creatine", "weight-management", "detox",
        "energy", "immunity", "joint-health"
    ]

    CERTIFICATIONS: List[str] = [
        "organic", "non-gmo", "vegan", "gluten-free", "gmp", "nsf",
        "kosher", "halal", "third-party-tested"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

### Acceptance Criteria:
- [ ] config.py exists
- [ ] All environment variables defined
- [ ] Pydantic validation works
- [ ] Default values set appropriately

---

## Task 1.10: Database Connection Module

**Priority:** Critical
**Estimated Time:** 1.5 hours
**Dependencies:** Task 1.8, 1.9

### Actions:

**Create `backend/database.py`**:
```python
"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### Acceptance Criteria:
- [ ] database.py exists
- [ ] Async engine configured
- [ ] Session factory created
- [ ] Dependency injection function `get_db()` works

---

## Task 1.11: SQLAlchemy Models

**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Task 1.10

### Actions:

**Create `backend/models/database.py`**:
```python
"""
SQLAlchemy ORM models
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, Float, ForeignKey, ARRAY, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base


class Lead(Base):
    """Lead model - stores contact form submissions"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, nullable=False)

    # Sender information
    sender_email = Column(String, nullable=False, index=True)
    sender_name = Column(String)
    company_name = Column(String)
    phone = Column(String)

    # Email content
    subject = Column(Text)
    body = Column(Text)
    received_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    processed_at = Column(TIMESTAMP(timezone=True), index=True)

    # Supplement-specific data
    product_type = Column(ARRAY(String))
    specific_ingredients = Column(ARRAY(String))
    delivery_format = Column(ARRAY(String))
    certifications_requested = Column(ARRAY(String))

    # Business intelligence
    estimated_quantity = Column(String)
    timeline_urgency = Column(String)
    budget_indicator = Column(String)
    experience_level = Column(String)
    distribution_channel = Column(ARRAY(String))
    has_existing_brand = Column(Boolean)

    # Lead scoring
    lead_quality_score = Column(Integer)
    response_priority = Column(String)

    # Additional metadata
    specific_questions = Column(ARRAY(String))
    geographic_region = Column(String)
    extraction_confidence = Column(Float)
    internal_notes = Column(Text)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('lead_quality_score >= 1 AND lead_quality_score <= 10', name='valid_quality_score'),
    )


class Draft(Base):
    """Draft model - stores generated email responses"""
    __tablename__ = "drafts"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)

    # Draft content
    subject_line = Column(String, nullable=False)
    draft_content = Column(Text, nullable=False)

    # Status and metadata
    status = Column(String, nullable=False, default="pending", index=True)
    response_type = Column(String)
    confidence_score = Column(Float)
    flags = Column(ARRAY(String))
    rag_sources = Column(ARRAY(String))

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    reviewed_at = Column(TIMESTAMP(timezone=True))
    approved_at = Column(TIMESTAMP(timezone=True))
    sent_at = Column(TIMESTAMP(timezone=True))

    # Approval workflow
    reviewed_by = Column(String)
    approval_feedback = Column(Text)
    edit_summary = Column(Text)

    # Learning data
    customer_replied = Column(Boolean)
    customer_sentiment = Column(String)


class DocumentEmbedding(Base):
    """Document embeddings for RAG system"""
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    # Document identification
    document_name = Column(String, nullable=False, index=True)
    document_type = Column(String, nullable=False, index=True)
    section_title = Column(String)

    # Content and embeddings
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    embedding = Column(Vector(1536))

    # Metadata
    metadata = Column(JSONB)
    is_active = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class ProductTypeTrend(Base):
    """Product type trends over time"""
    __tablename__ = "product_type_trends"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, nullable=False, index=True)
    date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    mention_count = Column(Integer, default=1)
    lead_count = Column(Integer, default=1)
    avg_quality_score = Column(Float)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class AnalyticsSnapshot(Base):
    """Analytics snapshots for historical reporting"""
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    period_type = Column(String, nullable=False)
    metrics = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
```

### Acceptance Criteria:
- [ ] All 5 models defined (Lead, Draft, DocumentEmbedding, ProductTypeTrend, AnalyticsSnapshot)
- [ ] Models match database schema from Task 1.6
- [ ] Proper indexes defined
- [ ] Timestamps auto-managed

---

## Task 1.12: Pydantic Schemas

**Priority:** High
**Estimated Time:** 2 hours
**Dependencies:** Task 1.11

### Actions:

**Create `backend/models/schemas.py`**:
```python
"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime


# Lead Schemas
class LeadBase(BaseModel):
    """Base lead schema"""
    sender_email: EmailStr
    sender_name: Optional[str] = None
    company_name: Optional[str] = None
    phone: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class LeadCreate(LeadBase):
    """Schema for creating a lead"""
    message_id: str
    received_at: datetime


class LeadExtracted(LeadBase):
    """Schema for lead with extracted data"""
    id: int
    message_id: str
    received_at: datetime
    processed_at: Optional[datetime] = None

    # Extracted data
    product_type: List[str] = []
    specific_ingredients: List[str] = []
    delivery_format: List[str] = []
    certifications_requested: List[str] = []

    # Business intelligence
    estimated_quantity: Optional[str] = None
    timeline_urgency: Optional[str] = None
    budget_indicator: Optional[str] = None
    experience_level: Optional[str] = None
    distribution_channel: List[str] = []
    has_existing_brand: Optional[bool] = None

    # Lead scoring
    lead_quality_score: Optional[int] = Field(None, ge=1, le=10)
    response_priority: Optional[str] = None

    # Metadata
    specific_questions: List[str] = []
    geographic_region: Optional[str] = None
    extraction_confidence: Optional[float] = None
    internal_notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Draft Schemas
class DraftBase(BaseModel):
    """Base draft schema"""
    subject_line: str
    draft_content: str


class DraftCreate(DraftBase):
    """Schema for creating a draft"""
    lead_id: int
    response_type: Optional[str] = None
    confidence_score: Optional[float] = None
    flags: List[str] = []
    rag_sources: List[str] = []


class DraftResponse(DraftBase):
    """Schema for draft response"""
    id: int
    lead_id: int
    status: str
    response_type: Optional[str] = None
    confidence_score: Optional[float] = None
    flags: List[str] = []
    rag_sources: List[str] = []

    created_at: datetime
    reviewed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    reviewed_by: Optional[str] = None
    approval_feedback: Optional[str] = None
    edit_summary: Optional[str] = None

    customer_replied: Optional[bool] = None
    customer_sentiment: Optional[str] = None

    class Config:
        from_attributes = True


class DraftUpdate(BaseModel):
    """Schema for updating a draft"""
    subject_line: Optional[str] = None
    draft_content: Optional[str] = None
    status: Optional[str] = None
    approval_feedback: Optional[str] = None
    edit_summary: Optional[str] = None


class DraftApproval(BaseModel):
    """Schema for draft approval action"""
    action: str = Field(..., pattern="^(approve|reject|edit)$")
    feedback: Optional[str] = None
    edited_content: Optional[str] = None
    reviewed_by: str


# Analytics Schemas
class ProductTypeTrendResponse(BaseModel):
    """Schema for product type trend"""
    product_type: str
    date: datetime
    mention_count: int
    lead_count: int
    avg_quality_score: Optional[float] = None

    class Config:
        from_attributes = True


class AnalyticsOverview(BaseModel):
    """Schema for analytics overview"""
    total_leads: int
    total_drafts: int
    avg_quality_score: float
    approval_rate: float
    leads_by_priority: dict
    leads_by_product_type: dict


# Knowledge Base Schemas
class DocumentUpload(BaseModel):
    """Schema for document upload"""
    document_name: str
    document_type: str = Field(..., pattern="^(product_catalog|pricing|certification|capability|faq)$")
    content: str


class DocumentEmbeddingResponse(BaseModel):
    """Schema for document embedding"""
    id: int
    document_name: str
    document_type: str
    section_title: Optional[str] = None
    chunk_text: str
    chunk_index: Optional[int] = None
    is_active: bool
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


# RAG Schemas
class RAGQuery(BaseModel):
    """Schema for RAG query"""
    query: str
    top_k: int = 10
    document_types: Optional[List[str]] = None
    min_similarity: float = 0.7


class RAGResult(BaseModel):
    """Schema for RAG result"""
    chunk_text: str
    document_name: str
    document_type: str
    section_title: Optional[str] = None
    similarity_score: float
```

### Acceptance Criteria:
- [ ] All pydantic schemas defined
- [ ] Proper validation rules
- [ ] Schemas match database models
- [ ] Request/response models separated

---

## Task 1.13: Frontend Dockerfile

**Priority:** High
**Estimated Time:** 30 minutes
**Dependencies:** Task 1.3

### Actions:

**Create `frontend/Dockerfile.dev`**:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Create `frontend/Dockerfile` (for production)**:
```dockerfile
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Acceptance Criteria:
- [ ] Development Dockerfile exists
- [ ] Production Dockerfile exists
- [ ] Both use Node 18
- [ ] Development server runs on port 3000

---

## Task 1.14: Frontend Package.json and Vite Setup

**Priority:** High
**Estimated Time:** 1 hour
**Dependencies:** Task 1.13

### Actions:

**Create `frontend/package.json`**:
```json
{
  "name": "supplement-lead-dashboard",
  "version": "2.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "@tanstack/react-query": "^5.14.2",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "date-fns": "^3.0.0",
    "react-hot-toast": "^2.4.1",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8",
    "eslint": "^8.55.0",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

**Create `frontend/vite.config.js`**:
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

**Create `frontend/tailwind.config.js`**:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        }
      }
    },
  },
  plugins: [],
}
```

**Create `frontend/postcss.config.js`**:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### Acceptance Criteria:
- [ ] package.json with all dependencies
- [ ] Vite configured
- [ ] TailwindCSS configured
- [ ] PostCSS configured

---

## Task 1.15: Frontend Basic Structure

**Priority:** High
**Estimated Time:** 2 hours
**Dependencies:** Task 1.14

### Actions:

**Create `frontend/index.html`**:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Supplement Lead Intelligence System</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**Create `frontend/src/main.jsx`**:
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App.jsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
```

**Create `frontend/src/index.css`**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Create `frontend/src/App.jsx`**:
```jsx
import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Inbox from './pages/Inbox'
import Analytics from './pages/Analytics'
import Leads from './pages/Leads'
import Knowledge from './pages/Knowledge'

function App() {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="inbox" element={<Inbox />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="leads" element={<Leads />} />
          <Route path="knowledge" element={<Knowledge />} />
        </Route>
      </Routes>
    </>
  )
}

export default App
```

**Create `frontend/src/services/api.js`**:
```javascript
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const leadsAPI = {
  getAll: (params) => api.get('/leads', { params }),
  getById: (id) => api.get(`/leads/${id}`),
  create: (data) => api.post('/leads', data),
  update: (id, data) => api.put(`/leads/${id}`, data),
}

export const draftsAPI = {
  getAll: (params) => api.get('/drafts', { params }),
  getById: (id) => api.get(`/drafts/${id}`),
  approve: (id, data) => api.post(`/drafts/${id}/approve`, data),
  reject: (id, data) => api.post(`/drafts/${id}/reject`, data),
  update: (id, data) => api.put(`/drafts/${id}`, data),
}

export const analyticsAPI = {
  getOverview: (params) => api.get('/analytics/overview', { params }),
  getProductTrends: (params) => api.get('/analytics/product-trends', { params }),
  export: (format, params) => api.get(`/analytics/export/${format}`, { params, responseType: 'blob' }),
}

export const knowledgeAPI = {
  getDocuments: () => api.get('/knowledge/documents'),
  upload: (formData) => api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  reindex: () => api.post('/knowledge/reindex'),
}

export default api
```

### Acceptance Criteria:
- [ ] index.html exists
- [ ] main.jsx with React Query setup
- [ ] App.jsx with routing
- [ ] API service module with all endpoints
- [ ] TailwindCSS imported

---

## Task 1.16: Test Docker Compose Setup

**Priority:** Critical
**Estimated Time:** 1 hour
**Dependencies:** All previous tasks in Phase 1

### Actions:

1. Build and start all services:
```bash
cd /var/www/emailagent
docker-compose build
docker-compose up -d
```

2. Verify all containers are running:
```bash
docker-compose ps
```

3. Check logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
docker-compose logs -f redis
```

4. Test endpoints:
```bash
# Health check
curl http://localhost:8001/health

# API docs
open http://localhost:8001/api/docs

# Frontend
open http://localhost:3001
```

5. Test database connection:
```bash
docker-compose exec postgres psql -U emailagent_user -d supplement_leads_db -c "\dt"
```

6. Test Redis:
```bash
docker-compose exec redis redis-cli ping
```

### Acceptance Criteria:
- [ ] All containers start successfully
- [ ] No port conflicts (verify ports 8001, 3001, 5434, 6380)
- [ ] Backend health check returns success
- [ ] API documentation accessible at http://localhost:8001/api/docs
- [ ] Frontend loads at http://localhost:3001
- [ ] PostgreSQL accessible and pgvector extension enabled
- [ ] Redis responds to PING

---

# PHASE 2: RAG System Implementation (Week 2)

## Task 2.1: Document Processing Module

**Priority:** Critical
**Estimated Time:** 3 hours
**Dependencies:** Phase 1 complete

### Actions:

**Create `backend/rag/document_processor.py`**:
```python
"""
Document processing for RAG system
Supports PDF, DOCX, Markdown, and plain text
"""
import PyPDF2
import docx
from typing import List, Dict
from pathlib import Path
import markdown
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process various document formats for RAG ingestion"""

    @staticmethod
    def read_pdf(file_path: str) -> str:
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            raise

    @staticmethod
    def read_docx(file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            doc = docx.Document(file_path)
            text = "\n\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {e}")
            raise

    @staticmethod
    def read_markdown(file_path: str) -> str:
        """Read markdown file and optionally convert to plain text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Return raw markdown (preserves structure better for chunking)
                return content.strip()
        except Exception as e:
            logger.error(f"Error reading Markdown {file_path}: {e}")
            raise

    @staticmethod
    def read_txt(file_path: str) -> str:
        """Read plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Error reading TXT {file_path}: {e}")
            raise

    @classmethod
    def process_document(cls, file_path: str) -> Dict[str, str]:
        """
        Process a document and return extracted text

        Args:
            file_path: Path to document

        Returns:
            Dict with document_name and content
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        logger.info(f"Processing document: {path.name}")

        if extension == '.pdf':
            content = cls.read_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            content = cls.read_docx(file_path)
        elif extension in ['.md', '.markdown']:
            content = cls.read_markdown(file_path)
        elif extension == '.txt':
            content = cls.read_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

        return {
            "document_name": path.stem,
            "content": content,
            "file_type": extension[1:]  # Remove the dot
        }
```

### Acceptance Criteria:
- [ ] DocumentProcessor class created
- [ ] Supports PDF, DOCX, Markdown, TXT
- [ ] Error handling for each format
- [ ] Returns standardized dict format

---

## Task 2.2: Text Chunking Module

**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Task 2.1

### Actions:

**Create `backend/rag/chunking.py`**:
```python
"""
Text chunking strategies for RAG
Uses tiktoken for token-based chunking
"""
import tiktoken
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """Chunk text into smaller pieces for embedding"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50, model: str = "cl100k_base"):
        """
        Initialize chunker

        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Number of overlapping tokens between chunks
            model: Tiktoken model name
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        try:
            self.encoding = tiktoken.get_encoding(model)
        except:
            logger.warning(f"Could not load encoding {model}, using cl100k_base")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Chunk text into smaller pieces

        Args:
            text: Text to chunk
            metadata: Optional metadata to include with each chunk

        Returns:
            List of chunks with metadata
        """
        if not text:
            return []

        # Encode text to tokens
        tokens = self.encoding.encode(text)

        if len(tokens) <= self.chunk_size:
            # Text is small enough, return as single chunk
            return [{
                "text": text,
                "chunk_index": 0,
                "token_count": len(tokens),
                **(metadata or {})
            }]

        chunks = []
        start_idx = 0
        chunk_idx = 0

        while start_idx < len(tokens):
            # Get chunk of tokens
            end_idx = min(start_idx + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            chunks.append({
                "text": chunk_text,
                "chunk_index": chunk_idx,
                "token_count": len(chunk_tokens),
                "start_token": start_idx,
                "end_token": end_idx,
                **(metadata or {})
            })

            # Move to next chunk with overlap
            start_idx += self.chunk_size - self.chunk_overlap
            chunk_idx += 1

        logger.info(f"Created {len(chunks)} chunks from {len(tokens)} tokens")
        return chunks

    def chunk_by_sections(self, text: str, section_delimiter: str = "\n\n", metadata: Dict = None) -> List[Dict]:
        """
        Chunk text by sections (e.g., paragraphs or headings)

        Args:
            text: Text to chunk
            section_delimiter: Delimiter that separates sections
            metadata: Optional metadata

        Returns:
            List of chunks
        """
        sections = text.split(section_delimiter)
        chunks = []
        current_chunk = ""
        chunk_idx = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Check if adding this section would exceed chunk size
            test_chunk = f"{current_chunk}\n\n{section}" if current_chunk else section
            token_count = self.count_tokens(test_chunk)

            if token_count <= self.chunk_size:
                current_chunk = test_chunk
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "chunk_index": chunk_idx,
                        "token_count": self.count_tokens(current_chunk),
                        **(metadata or {})
                    })
                    chunk_idx += 1

                # Start new chunk with current section
                current_chunk = section

        # Add final chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk,
                "chunk_index": chunk_idx,
                "token_count": self.count_tokens(current_chunk),
                **(metadata or {})
            })

        logger.info(f"Created {len(chunks)} chunks by sections")
        return chunks
```

### Acceptance Criteria:
- [ ] TextChunker class created
- [ ] Token-based chunking implemented
- [ ] Overlap functionality works
- [ ] Section-based chunking option available
- [ ] Metadata preserved in chunks

---

## Task 2.3: Embedding Generation Module

**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Task 2.2, config module

### Actions:

**Create `backend/rag/embeddings.py`**:
```python
"""
Embedding generation using Claude or OpenAI
"""
import anthropic
import openai
from typing import List
import logging
from config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text chunks"""

    def __init__(self, model: str = None):
        """
        Initialize embedding generator

        Args:
            model: "claude" or "openai". If None, uses settings.EMBEDDING_MODEL
        """
        self.model = model or settings.EMBEDDING_MODEL

        if self.model == "claude":
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        elif self.model == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key required for OpenAI embeddings")
            openai.api_key = settings.OPENAI_API_KEY
        else:
            raise ValueError(f"Unsupported embedding model: {self.model}")

        logger.info(f"Initialized embedding generator with model: {self.model}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            if self.model == "claude":
                # Note: Claude may not have direct embedding API yet
                # This is a placeholder - adjust when Claude embeddings are available
                # For now, we'll use OpenAI as fallback
                logger.warning("Claude embeddings not yet available, using OpenAI")
                return await self._generate_openai_embedding(text)
            elif self.model == "openai":
                return await self._generate_openai_embedding(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        response = await openai.Embedding.acreate(
            model="text-embedding-ada-002",
            input=text
        )
        return response['data'][0]['embedding']

    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

            batch_embeddings = []
            for text in batch:
                embedding = await self.generate_embedding(text)
                batch_embeddings.append(embedding)

            embeddings.extend(batch_embeddings)

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
```

### Acceptance Criteria:
- [ ] EmbeddingGenerator class created
- [ ] OpenAI embedding integration works
- [ ] Batch processing implemented
- [ ] Error handling for API failures
- [ ] Returns 1536-dimensional vectors

---

## Task 2.4: Vector Search Module

**Priority:** Critical
**Estimated Time:** 2.5 hours
**Dependencies:** Task 2.3, database models

### Actions:

**Create `backend/rag/retrieval.py`**:
```python
"""
Semantic search and retrieval using pgvector
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List, Dict, Optional
import logging
from models.database import DocumentEmbedding
from rag.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class VectorRetriever:
    """Retrieve relevant documents using vector similarity search"""

    def __init__(self, embedding_generator: EmbeddingGenerator):
        """
        Initialize retriever

        Args:
            embedding_generator: Instance of EmbeddingGenerator
        """
        self.embedding_generator = embedding_generator

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 10,
        document_types: Optional[List[str]] = None,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Perform semantic search

        Args:
            db: Database session
            query: Search query
            top_k: Number of results to return
            document_types: Filter by document types
            min_similarity: Minimum cosine similarity score

        Returns:
            List of relevant chunks with metadata
        """
        # Generate embedding for query
        query_embedding = await self.embedding_generator.generate_embedding(query)

        # Build query with vector similarity
        # pgvector uses <=> for cosine distance (lower is better)
        # Similarity = 1 - distance

        query_sql = """
            SELECT
                id,
                document_name,
                document_type,
                section_title,
                chunk_text,
                chunk_index,
                metadata,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM document_embeddings
            WHERE is_active = true
        """

        # Add document type filter if specified
        if document_types:
            placeholders = ','.join([f"'{dt}'" for dt in document_types])
            query_sql += f" AND document_type IN ({placeholders})"

        # Add similarity threshold and ordering
        query_sql += """
            AND (1 - (embedding <=> :query_embedding::vector)) >= :min_similarity
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
        """

        # Execute query
        result = await db.execute(
            text(query_sql),
            {
                "query_embedding": str(query_embedding),
                "min_similarity": min_similarity,
                "top_k": top_k
            }
        )

        rows = result.fetchall()

        # Format results
        results = []
        for row in rows:
            results.append({
                "id": row.id,
                "document_name": row.document_name,
                "document_type": row.document_type,
                "section_title": row.section_title,
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "metadata": row.metadata,
                "similarity_score": float(row.similarity)
            })

        logger.info(f"Found {len(results)} relevant chunks for query")
        return results

    async def get_context_for_response(
        self,
        db: AsyncSession,
        lead_data: Dict,
        top_k: int = 10
    ) -> Dict:
        """
        Get relevant context for generating email response

        Args:
            db: Database session
            lead_data: Extracted lead data
            top_k: Number of chunks to retrieve

        Returns:
            Dict with retrieved context and sources
        """
        # Build query from lead data
        query_parts = []

        if lead_data.get("product_type"):
            query_parts.append(f"Product types: {', '.join(lead_data['product_type'])}")

        if lead_data.get("specific_ingredients"):
            query_parts.append(f"Ingredients: {', '.join(lead_data['specific_ingredients'])}")

        if lead_data.get("certifications_requested"):
            query_parts.append(f"Certifications: {', '.join(lead_data['certifications_requested'])}")

        if lead_data.get("body"):
            # Add key parts of email body
            query_parts.append(lead_data["body"][:500])  # First 500 chars

        query = ". ".join(query_parts)

        # Search for relevant context
        results = await self.search(
            db=db,
            query=query,
            top_k=top_k,
            min_similarity=0.7
        )

        # Group by document type
        context_by_type = {}
        for result in results:
            doc_type = result["document_type"]
            if doc_type not in context_by_type:
                context_by_type[doc_type] = []
            context_by_type[doc_type].append(result)

        return {
            "chunks": results,
            "by_type": context_by_type,
            "sources": list(set([r["document_name"] for r in results]))
        }
```

### Acceptance Criteria:
- [ ] VectorRetriever class created
- [ ] Semantic search using pgvector works
- [ ] Cosine similarity calculation correct
- [ ] Document type filtering works
- [ ] Context assembly for response generation

---

## Task 2.5: Document Ingestion Pipeline

**Priority:** Critical
**Estimated Time:** 3 hours
**Dependencies:** Tasks 2.1-2.4

### Actions:

**Create `backend/rag/ingestion.py`**:
```python
"""
Document ingestion pipeline for RAG system
"""
from pathlib import Path
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from rag.document_processor import DocumentProcessor
from rag.chunking import TextChunker
from rag.embeddings import EmbeddingGenerator
from models.database import DocumentEmbedding
from config import settings

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into RAG system"""

    def __init__(self):
        self.processor = DocumentProcessor()
        self.chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.embedding_gen = EmbeddingGenerator()

    async def ingest_document(
        self,
        db: AsyncSession,
        file_path: str,
        document_type: str,
        metadata: Dict = None
    ) -> int:
        """
        Ingest a single document

        Args:
            db: Database session
            file_path: Path to document
            document_type: Type of document (product_catalog, pricing, etc.)
            metadata: Optional metadata

        Returns:
            Number of chunks created
        """
        logger.info(f"Ingesting document: {file_path}")

        # Step 1: Process document
        doc_data = self.processor.process_document(file_path)
        document_name = doc_data["document_name"]
        content = doc_data["content"]

        # Step 2: Chunk document
        chunks = self.chunker.chunk_by_sections(
            text=content,
            metadata={
                "document_name": document_name,
                "document_type": document_type,
                **(metadata or {})
            }
        )

        if not chunks:
            logger.warning(f"No chunks created for {document_name}")
            return 0

        # Step 3: Generate embeddings
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedding_gen.generate_embeddings_batch(texts)

        # Step 4: Store in database
        chunk_count = 0
        for chunk, embedding in zip(chunks, embeddings):
            doc_embedding = DocumentEmbedding(
                document_name=document_name,
                document_type=document_type,
                chunk_text=chunk["text"],
                chunk_index=chunk["chunk_index"],
                embedding=embedding,
                metadata={
                    "token_count": chunk["token_count"],
                    "file_type": doc_data["file_type"],
                    **(metadata or {})
                },
                is_active=True,
                version=1
            )
            db.add(doc_embedding)
            chunk_count += 1

        await db.commit()

        logger.info(f"Ingested {chunk_count} chunks from {document_name}")
        return chunk_count

    async def ingest_directory(
        self,
        db: AsyncSession,
        directory_path: str,
        document_type: str
    ) -> Dict[str, int]:
        """
        Ingest all documents in a directory

        Args:
            db: Database session
            directory_path: Path to directory
            document_type: Type of documents

        Returns:
            Dict mapping file names to chunk counts
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory_path}")

        results = {}

        # Find all supported files
        supported_extensions = ['.pdf', '.docx', '.doc', '.md', '.markdown', '.txt']
        files = []
        for ext in supported_extensions:
            files.extend(directory.glob(f"*{ext}"))

        logger.info(f"Found {len(files)} documents in {directory_path}")

        for file_path in files:
            try:
                chunk_count = await self.ingest_document(
                    db=db,
                    file_path=str(file_path),
                    document_type=document_type
                )
                results[file_path.name] = chunk_count
            except Exception as e:
                logger.error(f"Error ingesting {file_path.name}: {e}")
                results[file_path.name] = 0

        total_chunks = sum(results.values())
        logger.info(f"Ingested {total_chunks} total chunks from {len(files)} files")

        return results

    async def deactivate_document(
        self,
        db: AsyncSession,
        document_name: str,
        version: int = None
    ):
        """
        Deactivate a document (soft delete)

        Args:
            db: Database session
            document_name: Name of document to deactivate
            version: Optional version to deactivate
        """
        query = select(DocumentEmbedding).where(
            DocumentEmbedding.document_name == document_name,
            DocumentEmbedding.is_active == True
        )

        if version is not None:
            query = query.where(DocumentEmbedding.version == version)

        result = await db.execute(query)
        embeddings = result.scalars().all()

        for embedding in embeddings:
            embedding.is_active = False

        await db.commit()
        logger.info(f"Deactivated {len(embeddings)} chunks for {document_name}")
```

### Acceptance Criteria:
- [ ] DocumentIngestionPipeline class created
- [ ] Single document ingestion works
- [ ] Directory batch ingestion works
- [ ] Embeddings stored in database
- [ ] Document deactivation (soft delete) works

---

## Task 2.6: Knowledge Base Ingestion Script

**Priority:** High
**Estimated Time:** 1.5 hours
**Dependencies:** Task 2.5

### Actions:

**Create `scripts/ingest_knowledge.py`**:
```python
"""
Script to ingest knowledge base documents
Run this to populate the RAG system with initial documents
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import AsyncSessionLocal
from rag.ingestion import DocumentIngestionPipeline
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge"

# Map directories to document types
DOCUMENT_TYPE_MAPPING = {
    "products": "product_catalog",
    "pricing": "pricing",
    "capabilities": "capability",
    "certifications": "certification",
    "faq": "faq"
}


async def ingest_all_knowledge():
    """Ingest all knowledge base documents"""
    pipeline = DocumentIngestionPipeline()

    async with AsyncSessionLocal() as db:
        total_documents = 0
        total_chunks = 0

        for dir_name, doc_type in DOCUMENT_TYPE_MAPPING.items():
            dir_path = KNOWLEDGE_BASE_PATH / dir_name

            if not dir_path.exists():
                logger.warning(f"Directory not found: {dir_path}")
                continue

            logger.info(f"\n{'='*60}")
            logger.info(f"Ingesting {doc_type} documents from {dir_name}/")
            logger.info(f"{'='*60}\n")

            try:
                results = await pipeline.ingest_directory(
                    db=db,
                    directory_path=str(dir_path),
                    document_type=doc_type
                )

                # Print results
                for filename, chunk_count in results.items():
                    if chunk_count > 0:
                        logger.info(f"✓ {filename}: {chunk_count} chunks")
                        total_documents += 1
                        total_chunks += chunk_count
                    else:
                        logger.warning(f"✗ {filename}: Failed to ingest")

            except Exception as e:
                logger.error(f"Error ingesting directory {dir_name}: {e}")

        logger.info(f"\n{'='*60}")
        logger.info(f"INGESTION COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Total documents: {total_documents}")
        logger.info(f"Total chunks: {total_chunks}")
        logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(ingest_all_knowledge())
```

### Acceptance Criteria:
- [ ] Script exists at `scripts/ingest_knowledge.py`
- [ ] Ingests all directories in knowledge/
- [ ] Maps directories to correct document types
- [ ] Provides progress output
- [ ] Can be run from command line

---

## Task 2.7: Sample Knowledge Base Documents

**Priority:** High
**Estimated Time:** 2 hours
**Dependencies:** Task 1.1

### Actions:

Create sample documents in the knowledge base:

**1. Create `knowledge/products/probiotics.md`**:
```markdown
# Probiotic Supplement Manufacturing

## Overview
We manufacture high-quality probiotic supplements with clinically-studied strains and guaranteed potency.

## Available Strains
- Lactobacillus acidophilus
- Bifidobacterium lactis
- Lactobacillus plantarum
- Lactobacillus rhamnosus GG
- Saccharomyces boulardii

## CFU Ranges
- Standard: 10-50 billion CFU per serving
- High-potency: 50-100 billion CFU per serving
- Ultra-potency: 100+ billion CFU per serving

## Delivery Formats
- Vegetarian capsules (delayed-release available)
- Powder sachets
- Gummies (shelf-stable strains only)

## Certifications Available
- Organic
- Non-GMO
- Vegan
- Gluten-free
- GMP certified facility
- Third-party tested for potency

## Minimum Order Quantities
- Standard formulations: 1,000 units
- Custom formulations: 5,000 units
```

**2. Create `knowledge/products/electrolytes.md`**:
```markdown
# Electrolyte Supplement Manufacturing

## Overview
Custom electrolyte formulations for hydration, recovery, and performance.

## Standard Mineral Profile
- Sodium: 100-500mg
- Potassium: 100-400mg
- Magnesium: 50-200mg
- Calcium: 50-150mg

## Formats Available
- Powder (flavored or unflavored)
- Effervescent tablets
- Capsules
- Ready-to-mix packets

## Flavor Options
- Lemon-lime
- Orange
- Berry
- Tropical
- Unflavored
- Custom flavors available (MOQ 10,000 units)

## Additional Ingredients
Can add:
- B-vitamins
- Vitamin C
- Amino acids (BCAAs, taurine)
- Natural sweeteners (stevia, monk fruit)

## Minimum Order Quantities
- Standard flavors: 2,500 units
- Custom formulations: 10,000 units
```

**3. Create `knowledge/pricing/moq-pricing-guide.md`**:
```markdown
# Minimum Order Quantities and Pricing Guide

## MOQ by Product Category

### Capsules & Tablets
- Standard formulations: 1,000-5,000 units
- Custom formulations: 5,000-10,000 units
- Delayed-release capsules: 10,000 units minimum

### Powders
- Standard formulations: 2,500 units
- Custom formulations: 5,000 units
- Bulk powder (unflavored): 1,000 units

### Gummies
- Standard formulations: 5,000 units
- Custom shapes/flavors: 10,000 units

## Pricing Tiers

### Startup (1,000-5,000 units)
- Higher per-unit cost
- Standard packaging only
- Limited customization

### Mid-Market (5,000-20,000 units)
- Competitive pricing
- Custom labeling included
- Moderate customization options

### Enterprise (20,000+ units)
- Best pricing
- Full customization
- Priority production scheduling

## Lead Times
- Standard formulations: 4-6 weeks
- Custom formulations: 6-8 weeks
- Sample production: 2-3 weeks

## Payment Terms
- New customers: 50% deposit, 50% before shipment
- Established customers: Net 30 terms available
```

**4. Create `knowledge/certifications/available-certifications.md`**:
```markdown
# Available Certifications

## Facility Certifications
- GMP (Good Manufacturing Practices) - Certified
- NSF International - Certified
- FDA Registered Facility
- Organic Handling Certified

## Product Certifications We Can Provide

### Organic
- USDA Organic certification available
- Requires organic ingredient sourcing
- Additional cost: $500-1,000 per product
- Timeline: 6-8 weeks for certification

### Non-GMO
- Non-GMO Project Verified available
- Requires non-GMO ingredient verification
- Additional cost: $800-1,500 per product
- Timeline: 8-10 weeks

### Vegan
- Vegan certification available
- All ingredients must be plant-based
- Additional cost: $300-500 per product
- Timeline: 4-6 weeks

### Gluten-Free
- Certified gluten-free available
- Testing required
- Additional cost: $400-600 per product
- Timeline: 4-6 weeks

### Kosher & Halal
- Available upon request
- Requires specialized handling
- Additional cost: $1,000-2,000 per product
- Timeline: 8-12 weeks

## Third-Party Testing
All products include:
- Potency testing
- Purity testing
- Heavy metals screening
- Microbiological testing

COA (Certificate of Analysis) provided with every batch.
```

**5. Create `knowledge/faq/common-questions.md`**:
```markdown
# Frequently Asked Questions

## How long does the manufacturing process take?
Standard formulations: 4-6 weeks from order to delivery
Custom formulations: 6-8 weeks from formula approval to delivery
This includes production, testing, and packaging.

## Can I get samples before placing a large order?
Yes! We can produce samples of your formulation.
Sample production: 2-3 weeks
Sample cost: $500-1,500 depending on complexity
Sample units provided: 50-100 units

## What are your minimum order quantities?
MOQs vary by product type:
- Capsules: 1,000-5,000 units
- Powders: 2,500-5,000 units
- Gummies: 5,000-10,000 units
Custom formulations generally have higher MOQs.

## Do you provide packaging and labeling?
Yes! We offer:
- Stock bottles (various sizes)
- Custom labeled bottles
- Full custom packaging design (additional cost, higher MOQs)
- Blister packaging for tablets/capsules

## Can you match an existing formula?
Yes, we can reverse-engineer existing formulations.
Provide us with:
- Supplement facts label
- Full ingredient list
- Any specific requirements
We'll provide a comparable formula and quote.

## What certifications are available?
We can provide:
- Organic (USDA)
- Non-GMO Project Verified
- Vegan
- Gluten-Free
- Kosher
- Halal
Additional costs and timelines apply.

## Do you ship internationally?
Yes, we ship worldwide.
International shipping considerations:
- Customs documentation provided
- Compliance with destination country regulations
- Additional shipping costs apply
- Import duties are customer's responsibility
```

### Acceptance Criteria:
- [ ] 5 knowledge base documents created
- [ ] Documents cover all key areas (products, pricing, certifications, FAQ)
- [ ] Markdown formatting correct
- [ ] Content is realistic and detailed enough for RAG

---

## Task 2.8: Test RAG System End-to-End

**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** Tasks 2.6, 2.7

### Actions:

1. **Run ingestion script**:
```bash
cd /var/www/emailagent
docker-compose exec backend python ../scripts/ingest_knowledge.py
```

2. **Verify embeddings in database**:
```bash
docker-compose exec postgres psql -U emailagent_user -d supplement_leads_db -c "SELECT document_type, COUNT(*) FROM document_embeddings GROUP BY document_type;"
```

3. **Create test script** `backend/test_rag.py`:
```python
"""Test RAG system"""
import asyncio
from database import AsyncSessionLocal
from rag.retrieval import VectorRetriever
from rag.embeddings import EmbeddingGenerator

async def test_retrieval():
    embedding_gen = EmbeddingGenerator()
    retriever = VectorRetriever(embedding_gen)

    test_queries = [
        "What probiotics do you offer?",
        "What are your minimum order quantities?",
        "Do you have organic certification?",
        "Can you make custom electrolyte formulations?"
    ]

    async with AsyncSessionLocal() as db:
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")

            results = await retriever.search(db, query, top_k=3)

            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Document: {result['document_name']} ({result['document_type']})")
                print(f"Similarity: {result['similarity_score']:.3f}")
                print(f"Text preview: {result['chunk_text'][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
```

4. **Run test**:
```bash
docker-compose exec backend python test_rag.py
```

### Acceptance Criteria:
- [ ] Ingestion script runs successfully
- [ ] At least 50 chunks ingested
- [ ] All 5 document types represented
- [ ] Test queries return relevant results
- [ ] Similarity scores > 0.7 for relevant matches
- [ ] No errors in logs

---

# PHASE 3: Agents & Background Processing (Week 3)

## Task 3.1: Extraction Agent Implementation

**Priority:** Critical
**Estimated Time:** 6 hours
**Dependencies:** Phase 2 complete, RAG system working

### Objectives:
Implement the Extraction Agent that analyzes contact form emails and extracts supplement-specific data using Claude API and RAG enhancement.

### Key Deliverables:
- `backend/agents/extraction_agent.py` - Main extraction agent class
- Extract all 15+ data fields as per PRD:
  - Product types (probiotics, electrolytes, protein, etc.)
  - Specific ingredients
  - Delivery format preferences
  - Certifications requested
  - Lead quality score (1-10)
  - Timeline urgency, budget indicators
  - Experience level, distribution channels
  - Geographic region, specific questions
- Use RAG to enhance understanding of technical terms
- Return structured JSON with confidence scores

### Acceptance Criteria:
- [ ] Extraction agent successfully processes sample emails
- [ ] All supplement-specific fields extracted
- [ ] Lead quality scoring algorithm works (1-10 scale)
- [ ] Uses RAG for context when encountering industry jargon
- [ ] Returns confidence score for extraction
- [ ] Error handling for malformed emails

---

## Task 3.2: Response Agent Implementation

**Priority:** Critical
**Estimated Time:** 6 hours
**Dependencies:** Task 3.1, RAG retrieval working

### Objectives:
Implement the Response Agent that generates contextual email responses using RAG-retrieved knowledge base content.

### Key Deliverables:
- `backend/agents/response_agent.py` - Main response generation agent
- Generate professional B2B responses using Claude API
- Retrieve relevant context from knowledge base via RAG
- Include source attribution (which documents used)
- Calculate confidence score for each response
- Flag responses requiring special attention (complex formulations, pricing negotiations)
- Maintain consistent professional tone

### Acceptance Criteria:
- [ ] Generates appropriate responses for various inquiry types
- [ ] References accurate information from knowledge base
- [ ] Includes source attribution (document names)
- [ ] Confidence score calculated (0-10)
- [ ] Flags complex requests appropriately
- [ ] Professional B2B tone maintained
- [ ] No hallucinated information (all facts from RAG)

---

## Task 3.3: Analytics Agent Implementation

**Priority:** High
**Estimated Time:** 4 hours
**Dependencies:** Database models, Task 3.1

### Objectives:
Implement the Analytics Agent that processes lead data to generate insights and trends.

### Key Deliverables:
- `backend/agents/analytics_agent.py` - Analytics calculation logic
- Calculate product type trends over time
- Generate lead quality distributions
- Identify trending ingredients and certifications
- Create daily/weekly/monthly snapshots
- Store in `analytics_snapshots` table

### Acceptance Criteria:
- [ ] Calculates statistics from leads table
- [ ] Generates product type trends
- [ ] Creates analytics snapshots in database
- [ ] Handles empty data gracefully
- [ ] Can generate reports for custom date ranges

---

## Task 3.4: Celery Task Setup

**Priority:** Critical
**Estimated Time:** 4 hours
**Dependencies:** Tasks 3.1, 3.2, 3.3

### Objectives:
Set up Celery background job processing for email monitoring and agent execution.

### Key Deliverables:
- `backend/tasks/celery_app.py` - Celery configuration
- `backend/tasks/workers.py` - Background task definitions
- Email monitoring task (runs every 60 seconds)
- Lead processing task (extraction + response generation)
- Analytics snapshot generation task (daily)

### Task Functions Needed:
1. `monitor_inbox()` - Check for new emails via Email MCP
2. `process_lead(lead_id)` - Run extraction agent
3. `generate_draft(lead_id)` - Run response agent
4. `generate_analytics_snapshot()` - Run analytics agent
5. `cleanup_old_data()` - Data retention

### Acceptance Criteria:
- [ ] Celery workers start successfully
- [ ] Celery beat scheduler working
- [ ] Email monitoring task runs every 60 seconds
- [ ] Tasks can be triggered manually for testing
- [ ] Error handling and retry logic implemented
- [ ] Logs show task execution

---

## Task 3.5: Email MCP Integration

**Priority:** Critical
**Estimated Time:** 5 hours
**Dependencies:** Task 3.4

### Objectives:
Integrate Email MCP Server for reading contact form emails and sending responses.

### Key Deliverables:
- `backend/services/email_monitor.py` - Email monitoring service
- Connect to IMAP to read emails
- Parse email content and metadata
- Create Lead records in database
- Mark emails as processed
- Send responses via SMTP

### Functions Needed:
- `connect_imap()` - Connect to email server
- `fetch_new_emails()` - Get unread emails
- `parse_email(raw_email)` - Extract sender, subject, body
- `create_lead_from_email(email_data)` - Store in database
- `send_email(to, subject, body)` - Send via SMTP
- `mark_as_read(message_id)` - Update email status

### Acceptance Criteria:
- [ ] Successfully connects to email inbox
- [ ] Fetches new emails
- [ ] Creates Lead records from emails
- [ ] Handles connection errors gracefully
- [ ] Can send emails via SMTP
- [ ] Email credentials loaded from environment

---

## Task 3.6: API Endpoints for Leads

**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** Database models, agents

### Objectives:
Create FastAPI endpoints for lead management.

### Key Deliverables:
- `backend/api/leads.py` - Lead CRUD endpoints
- GET /api/leads - List all leads (with filters)
- GET /api/leads/{id} - Get single lead with details
- PUT /api/leads/{id} - Update lead (add notes, etc.)
- POST /api/leads/{id}/reprocess - Rerun extraction agent

### Acceptance Criteria:
- [ ] All endpoints functional
- [ ] Pagination working (20 items per page)
- [ ] Filtering by product type, quality score, date range
- [ ] Sorting options (newest first, highest quality, etc.)
- [ ] Returns proper error codes
- [ ] API documentation in /api/docs

---

## Task 3.7: API Endpoints for Drafts

**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** Database models, Task 3.2

### Objectives:
Create FastAPI endpoints for draft management and approval workflow.

### Key Deliverables:
- `backend/api/drafts.py` - Draft management endpoints
- GET /api/drafts - List pending drafts
- GET /api/drafts/{id} - Get draft with lead context
- PUT /api/drafts/{id} - Update draft content
- POST /api/drafts/{id}/approve - Approve and send
- POST /api/drafts/{id}/reject - Reject with feedback
- POST /api/drafts/{id}/regenerate - Regenerate with new context

### Acceptance Criteria:
- [ ] All endpoints functional
- [ ] Approval workflow working end-to-end
- [ ] Edited drafts saved correctly
- [ ] Rejection feedback stored for learning
- [ ] Email sent successfully on approval
- [ ] Draft status updated appropriately

---

## Task 3.8: End-to-End Workflow Testing

**Priority:** Critical
**Estimated Time:** 3 hours
**Dependencies:** All Phase 3 tasks

### Objectives:
Test the complete email → lead → draft → approval → send workflow.

### Test Scenarios:
1. Send test email to monitored inbox
2. Verify Celery picks it up
3. Verify extraction agent processes it
4. Verify response agent generates draft
5. Verify draft appears in database with status "pending"
6. Use API to approve draft
7. Verify email sent to sender
8. Verify draft status updated to "sent"

### Create Test Script:
- `backend/test_workflow.py` - End-to-end workflow test

### Acceptance Criteria:
- [ ] Test email processed automatically
- [ ] Lead created with extracted data
- [ ] Draft generated with RAG context
- [ ] Draft can be approved via API
- [ ] Response email sent successfully
- [ ] All statuses updated correctly
- [ ] No errors in logs

---

# PHASE 4: Web Approval Interface (Week 4)

## Task 4.1: Frontend Layout Component

**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** Phase 1 frontend setup

### Objectives:
Create main layout component with navigation and routing.

### Key Deliverables:
- `frontend/src/components/Layout.jsx` - Main layout with navbar
- Navigation menu: Overview, Inbox, Analytics, Leads, Knowledge
- Show pending draft count in Inbox badge
- Responsive sidebar/header
- Logout functionality placeholder

### Acceptance Criteria:
- [ ] Layout renders on all pages
- [ ] Navigation works (React Router)
- [ ] Pending count badge shows live data
- [ ] Responsive design (desktop + tablet)
- [ ] Clean, professional UI using TailwindCSS

---

## Task 4.2: Dashboard Overview Page

**Priority:** High
**Estimated Time:** 4 hours
**Dependencies:** Task 4.1, analytics API

### Objectives:
Create overview dashboard with key metrics and charts.

### Key Deliverables:
- `frontend/src/pages/Dashboard.jsx` - Overview page
- Metrics cards: Total leads, Pending drafts, Avg quality score, Approval rate
- Product type distribution pie chart (Recharts)
- Lead quality over time line chart
- Recent activity feed (last 10 leads/drafts)

### Acceptance Criteria:
- [ ] All metrics display correctly
- [ ] Charts render with real data
- [ ] Auto-refresh every 30 seconds
- [ ] Loading states handled
- [ ] Responsive layout

---

## Task 4.3: Inbox Page - Pending Drafts List

**Priority:** Critical
**Estimated Time:** 5 hours
**Dependencies:** Task 4.1, drafts API

### Objectives:
Create inbox page showing pending drafts queue.

### Key Deliverables:
- `frontend/src/pages/Inbox.jsx` - Main inbox page
- `frontend/src/components/DraftQueue.jsx` - Sidebar with pending drafts
- List drafts with priority badges, sender, timestamp
- Filter by priority (critical, high, medium, low)
- Sort by newest, oldest, highest confidence
- Click draft to show in main panel

### Acceptance Criteria:
- [ ] Drafts list displays correctly
- [ ] Filtering works
- [ ] Sorting works
- [ ] Selection highlights draft
- [ ] Shows confidence score and flags
- [ ] Real-time updates when draft status changes

---

## Task 4.4: Draft Review Component

**Priority:** Critical
**Estimated Time:** 6 hours
**Dependencies:** Task 4.3

### Objectives:
Create split-panel draft review interface with original email and generated response.

### Key Deliverables:
- `frontend/src/components/DraftReview.jsx` - Main review component
- Left panel: Original email with extracted data display
- Right panel: Generated draft with inline editing
- Show confidence score, flags, RAG sources used
- Action buttons: Approve, Edit & Send, Reject, Save for Later

### Features:
- Inline text editor for draft (simple textarea or rich text)
- Show which knowledge base documents were used
- Display extracted lead data (product types, certifications, etc.)
- Subject line editing
- Preview mode before sending

### Acceptance Criteria:
- [ ] Both panels render correctly
- [ ] Inline editing works smoothly
- [ ] RAG sources displayed with links
- [ ] All action buttons functional
- [ ] Confirmation dialog before sending
- [ ] Error handling for send failures

---

## Task 4.5: Draft Approval Workflow

**Priority:** Critical
**Estimated Time:** 4 hours
**Dependencies:** Task 4.4

### Objectives:
Implement approval action handlers and email sending confirmation.

### Key Deliverables:
- Approve action: Call API, show success toast, remove from queue
- Edit & Send action: Save edits, call API, send
- Reject action: Show feedback modal, submit reason
- Modal components for confirmation and feedback

### Acceptance Criteria:
- [ ] Approve action works end-to-end
- [ ] Email sent successfully
- [ ] Edit functionality saves changes before sending
- [ ] Reject modal collects feedback
- [ ] Success/error notifications shown
- [ ] Draft removed from pending queue after action
- [ ] Loading states during API calls

---

## Task 4.6: Leads Browser Page

**Priority:** Medium
**Estimated Time:** 4 hours
**Dependencies:** Task 4.1, leads API

### Objectives:
Create leads browser with search, filter, and detail view.

### Key Deliverables:
- `frontend/src/pages/Leads.jsx` - Leads list page
- `frontend/src/components/LeadCard.jsx` - Lead summary card
- `frontend/src/components/LeadDetail.jsx` - Lead detail modal
- Search by email, company name
- Filter by product type, quality score, date range
- Sort options (newest, highest quality, etc.)
- Pagination (20 per page)

### Acceptance Criteria:
- [ ] Leads list displays correctly
- [ ] Search works (debounced)
- [ ] Filters apply correctly
- [ ] Pagination works
- [ ] Click lead to see full details
- [ ] Shows all extracted data fields

---

## Task 4.7: Knowledge Base Management Page

**Priority:** Medium
**Estimated Time:** 3 hours
**Dependencies:** Task 4.1, knowledge API

### Objectives:
Create knowledge base document management interface.

### Key Deliverables:
- `frontend/src/pages/Knowledge.jsx` - Knowledge management page
- List all ingested documents by type
- Show chunk count, last updated date
- Upload new document form
- Re-index button
- Document usage statistics (which docs referenced most)

### Acceptance Criteria:
- [ ] Documents list displays correctly
- [ ] Upload form works (file input + metadata)
- [ ] Re-index button triggers backend ingestion
- [ ] Usage stats show most referenced docs
- [ ] Loading states during upload/re-index

---

## Task 4.8: UI Polish and Error Handling

**Priority:** Medium
**Estimated Time:** 3 hours
**Dependencies:** All frontend pages

### Objectives:
Add polish, loading states, error handling, and notifications.

### Key Deliverables:
- Loading spinners for all async operations
- Error boundary components
- Toast notifications for all user actions (react-hot-toast)
- Empty states when no data
- Confirmation dialogs for destructive actions
- Keyboard shortcuts for inbox (approve, reject, next)

### Acceptance Criteria:
- [ ] All pages have loading states
- [ ] Errors displayed user-friendly
- [ ] Success/error toasts for all actions
- [ ] Empty states look good
- [ ] Keyboard shortcuts work in inbox
- [ ] No console errors

---

# PHASE 5: Analytics Dashboard & Production Polish (Week 5)

## Task 5.1: Analytics Page Implementation

**Priority:** High
**Estimated Time:** 6 hours
**Dependencies:** Analytics agent, analytics API

### Objectives:
Create comprehensive analytics page with visualizations.

### Key Deliverables:
- `frontend/src/pages/Analytics.jsx` - Main analytics page
- Product type trends line chart (time series)
- Certification requests heatmap
- Lead quality distribution bar chart
- Timeline urgency breakdown pie chart
- Top ingredients mentioned (bar chart)
- Date range selector (last 7 days, 30 days, 90 days, custom)
- Export to CSV button

### Charts to Implement:
1. Product type trends over time (line chart)
2. Certifications requested (horizontal bar chart)
3. Lead quality distribution (histogram)
4. Timeline urgency (pie chart)
5. Top 10 ingredients (bar chart)
6. Geographic distribution (if data available)

### Acceptance Criteria:
- [ ] All charts render with real data
- [ ] Date range filtering works
- [ ] Charts update when filters change
- [ ] Export to CSV downloads correct data
- [ ] Responsive chart sizing
- [ ] Interactive tooltips on charts

---

## Task 5.2: Analytics API Endpoints

**Priority:** High
**Estimated Time:** 4 hours
**Dependencies:** Analytics agent

### Objectives:
Create API endpoints for analytics data and exports.

### Key Deliverables:
- `backend/api/analytics.py` - Analytics endpoints
- GET /api/analytics/overview - High-level metrics
- GET /api/analytics/product-trends - Product type trends
- GET /api/analytics/certifications - Certification requests
- GET /api/analytics/lead-quality - Quality distribution
- GET /api/analytics/export/csv - Export data to CSV
- GET /api/analytics/export/pdf - Export report to PDF (optional)

### Acceptance Criteria:
- [ ] All endpoints return correct data
- [ ] Date range filtering works (query params)
- [ ] CSV export includes all relevant data
- [ ] Proper HTTP headers for downloads
- [ ] Caching for expensive queries (Redis)

---

## Task 5.3: Performance Optimization

**Priority:** High
**Estimated Time:** 4 hours
**Dependencies:** All previous tasks

### Objectives:
Optimize database queries, API responses, and frontend rendering.

### Key Actions:
- Add database indexes for common queries
- Implement query result caching (Redis)
- Optimize RAG retrieval queries
- Frontend: React.memo for expensive components
- Frontend: Lazy loading for charts
- Backend: Connection pooling tuning
- Reduce API payload sizes

### Performance Targets (from PRD):
- Lead processing: < 7 seconds
- Draft generation: < 15 seconds
- Dashboard page load: < 1 second
- API response times: < 500ms

### Acceptance Criteria:
- [ ] All performance targets met
- [ ] No slow queries (check pg_stat_statements)
- [ ] Frontend renders smoothly
- [ ] Charts load quickly
- [ ] No memory leaks

---

## Task 5.4: Logging and Monitoring

**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** All backend services

### Objectives:
Implement comprehensive logging and health monitoring.

### Key Deliverables:
- Structured logging throughout backend (structlog)
- Health check endpoints for all services
- Monitoring dashboard (optional: Prometheus + Grafana)
- Error tracking (optional: Sentry integration)
- Log rotation configuration

### Health Endpoints:
- GET /health - Overall system health
- GET /health/database - Database connection status
- GET /health/redis - Redis connection status
- GET /health/email - Email server connection status

### Acceptance Criteria:
- [ ] All errors logged with context
- [ ] Health checks return correct status
- [ ] Logs rotated properly (max 100MB)
- [ ] Error tracking working (if Sentry enabled)
- [ ] Can diagnose issues from logs

---

## Task 5.5: Testing Suite

**Priority:** High
**Estimated Time:** 5 hours
**Dependencies:** All components

### Objectives:
Create comprehensive test suite for backend and frontend.

### Key Deliverables:
- Backend unit tests (pytest)
  - Test agents individually
  - Test RAG retrieval
  - Test API endpoints
  - Test database operations
- Frontend component tests (if time allows)
- Integration tests for workflows
- Test coverage report

### Test Files:
- `tests/test_extraction_agent.py`
- `tests/test_response_agent.py`
- `tests/test_rag_system.py`
- `tests/test_api_endpoints.py`
- `tests/test_email_integration.py`

### Acceptance Criteria:
- [ ] Test coverage > 70% for critical paths
- [ ] All agent tests passing
- [ ] RAG retrieval tests passing
- [ ] API endpoint tests passing
- [ ] CI/CD ready (GitHub Actions config optional)

---

## Task 5.6: Documentation

**Priority:** Medium
**Estimated Time:** 4 hours
**Dependencies:** All tasks complete

### Objectives:
Create comprehensive user and technical documentation.

### Key Deliverables:
- `README.md` - Project overview, setup instructions
- `docs/USER_GUIDE.md` - How to use the dashboard
- `docs/DEPLOYMENT.md` - Production deployment guide
- `docs/API.md` - API documentation (supplement FastAPI auto-docs)
- `docs/MAINTENANCE.md` - Ongoing maintenance tasks
- Code comments and docstrings throughout

### Documentation Sections:
1. Quick start guide
2. Environment setup
3. Docker Compose usage
4. Knowledge base management
5. Troubleshooting common issues
6. API authentication (if implemented)
7. Backup and restore procedures
8. Monitoring and alerts setup

### Acceptance Criteria:
- [ ] README includes setup instructions
- [ ] User guide explains all features
- [ ] Deployment guide tested
- [ ] API documentation complete
- [ ] All public functions have docstrings

---

## Task 5.7: Production Deployment Preparation

**Priority:** High
**Estimated Time:** 4 hours
**Dependencies:** Task 5.6

### Objectives:
Prepare system for production deployment.

### Key Actions:
- Create production docker-compose.yml
- Set up Nginx configuration for reverse proxy
- SSL certificate setup (Let's Encrypt)
- Production environment variables template
- Database backup script
- Automated backup schedule (cron)
- Security hardening checklist
- Rate limiting on API endpoints

### Production Checklist:
- [ ] DEBUG=false in production
- [ ] Strong SECRET_KEY generated
- [ ] Database credentials secured
- [ ] SSL/HTTPS enabled
- [ ] CORS configured for production domain
- [ ] Firewall rules (only expose 80, 443)
- [ ] Automated backups configured
- [ ] Log aggregation set up
- [ ] Monitoring configured
- [ ] Rate limiting active

### Acceptance Criteria:
- [ ] Production deployment successful on test server
- [ ] HTTPS working
- [ ] All services start automatically
- [ ] Backups running daily
- [ ] Can recover from backup
- [ ] Security audit checklist complete

---

## Task 5.8: Final Testing and Bug Fixes

**Priority:** Critical
**Estimated Time:** 4 hours
**Dependencies:** All tasks complete

### Objectives:
Comprehensive testing and bug fixing before production launch.

### Test Scenarios:
1. Process 50 test emails end-to-end
2. Approve, reject, and edit various drafts
3. Verify all analytics update correctly
4. Test edge cases (malformed emails, API failures)
5. Load testing (simulate 100 emails/day)
6. Browser compatibility (Chrome, Firefox, Safari)
7. Mobile responsiveness testing
8. 7-day stability test (system running continuously)

### Acceptance Criteria (PRD Section 14):
- [ ] System monitors inbox continuously
- [ ] Data extraction >90% accuracy (manual review of 50 emails)
- [ ] Draft approval rate >70%
- [ ] All 5 dashboard pages functional
- [ ] RAG relevance >85%
- [ ] Performance meets NFR requirements
- [ ] System runs 7 days without critical errors
- [ ] Documentation complete

---

# FINAL CHECKLIST

## Production Readiness Criteria

### Technical
- [ ] All Phase 1-5 tasks complete
- [ ] Test coverage >70%
- [ ] Performance targets met
- [ ] Security review completed
- [ ] Database backups working
- [ ] Monitoring operational
- [ ] Documentation complete

### Functional
- [ ] Email monitoring working
- [ ] Lead extraction accurate (>90%)
- [ ] Response generation uses RAG correctly
- [ ] Approval workflow functional
- [ ] Analytics accurate
- [ ] Export features working

### Operational
- [ ] Docker Compose starts all services
- [ ] No port conflicts
- [ ] Logs accessible and rotated
- [ ] Health checks passing
- [ ] Error alerts configured
- [ ] Backup/restore tested

### User Acceptance
- [ ] User guide reviewed
- [ ] All 5 dashboard pages work
- [ ] Inbox workflow intuitive
- [ ] Charts display correctly
- [ ] No critical bugs
- [ ] Performance acceptable

---

## Total Estimated Time: 200 hours (5 weeks)

- **Phase 1:** ~20 hours
- **Phase 2:** ~20 hours
- **Phase 3:** ~34 hours
- **Phase 4:** ~32 hours
- **Phase 5:** ~34 hours
- **Buffer:** ~60 hours built into estimates

---

## Next Steps After Completion

1. **Staging Testing:** Deploy to staging environment
2. **User Training:** Train NutriCraft Labs team on usage
3. **Soft Launch:** Monitor first 100 leads closely
4. **Feedback Collection:** Gather user feedback
5. **Iteration:** Implement improvements based on feedback
6. **Progressive Automation:** Begin tracking metrics for auto-approval

---

**End of Task List**
