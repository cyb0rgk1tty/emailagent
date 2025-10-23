# Supplement Lead Intelligence System

**Version:** 2.2.0
**Company:** Nutricraft Labs
**Status:** Production Ready

## Overview

AI-powered lead intelligence system for supplement manufacturing that monitors contact form emails, extracts business intelligence using PydanticAI, generates RAG-enhanced draft responses, and provides analytics on product interests and market trends.

## Key Features

- 🤖 **PydanticAI Multi-Agent System**: Type-safe extraction, response, and analytics agents
- 🔄 **OpenRouter Integration**: Flexible LLM provider with Claude 4.5 models
- 📚 **RAG-Enhanced Responses**: Knowledge base-powered accurate responses
- 🧠 **Historical Response Learning**: Backfill past emails to teach AI your writing style
- 📊 **Business Intelligence**: Supplement-specific data extraction and analytics
- ✅ **Human-in-the-Loop**: Web-based approval workflow
- 📈 **Analytics Dashboard**: Product trends, lead quality, market insights
- 🔍 **Vector Search**: PostgreSQL with pgvector for semantic search
- 🛡️ **Type Safety**: Pydantic models with automatic validation and retries
- 🧵 **Email Thread Tracking**: Conversation threading, duplicate detection, reply handling
- 💼 **Complete Dashboard**: Analytics, leads browser, knowledge base management

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** (async API)
- **PydanticAI 1.0.5** (AI agent framework with structured outputs)
- **OpenRouter** (LLM provider - Claude 4.5 Sonnet/Haiku)
- **PostgreSQL 15+ with pgvector** (vector database)
- **SQLAlchemy 2.0** (async ORM)
- **Celery + Redis** (background jobs)

### Frontend
- **React 18**
- **Vite**
- **TailwindCSS**
- **React Query**
- **Recharts** (data visualization)

### Infrastructure
- **Docker & Docker Compose**
- **Nginx** (production)
- **Alembic** (database migrations)

## AI Agent Architecture

### PydanticAI Agents

The system uses **PydanticAI** for type-safe, reliable AI agent operations:

#### 1. Extraction Agent
- **Model**: Claude 4.5 Haiku (fast, cost-effective)
- **Output**: `LeadExtraction` Pydantic model
- **Features**:
  - Structured data extraction from emails
  - Lead quality scoring (1-10)
  - Priority classification (critical/high/medium/low)
  - Automatic validation and retries
- **Tools**:
  - `search_knowledge_base()` - RAG semantic search
  - `validate_product_type()` - Product validation
- **Temperature**: 0.3 (precise extraction)

#### 2. Response Agent
- **Model**: Claude 4.5 Sonnet (high-quality responses)
- **Output**: `ResponseDraft` Pydantic model
- **Features**:
  - Dynamic system prompts based on lead priority
  - RAG-powered context retrieval
  - Email format validation
  - Confidence scoring (0-10)
- **Tools**:
  - `search_knowledge_base()` - Targeted knowledge search
  - `get_comprehensive_context()` - Automatic context building
- **Temperature**: 0.7 (natural writing)

#### 3. Analytics Agent
- **Type**: Pure Python (no LLM required)
- **Features**:
  - Product trend tracking
  - Lead quality analytics
  - Daily snapshots
  - Market insights

### Type Safety & Validation

All agent outputs are validated by Pydantic models:
- **Automatic validation**: Invalid data is rejected
- **Retry mechanism**: 2 attempts on validation failure
- **Fallback systems**: Graceful degradation
- **Type hints**: Full IDE support

## Dashboard Features

The React-based dashboard provides a complete management interface:

### 📊 Analytics Page (`/analytics`)
- **Interactive Charts**: Priority distribution (pie), quality scores (bar), product types (horizontal bar), timeline trends (line)
- **Time Range Filters**: 7, 14, 30, or 90 days
- **Key Metrics**: Total leads, avg quality score, approval rate, pending review
- **Recent Activity Feed**: Real-time activity stream with timestamps
- **Powered by**: Recharts library for beautiful, responsive visualizations

### 📥 Inbox Page (`/inbox`)
- **Draft Review**: Approve, reject, or edit AI-generated email responses
- **Quick Actions**: One-click approve/reject with confirmation
- **Status Filtering**: Pending, approved, rejected, sent, all drafts
- **Confidence Scoring**: See AI confidence for each draft (0-10)
- **Lead Context**: View full lead details with each draft
- **Auto-Refresh**: Updates every 30 seconds

### 🔍 Leads Page (`/leads`)
- **Powerful Search**: Filter by email, name, company, subject, or body content
- **Multi-Filter System**: Priority (critical/high/medium/low), status (new/responded/customer_replied/etc.)
- **Sort Options**: By date, quality score, or priority
- **Lead Details Modal**: Full lead information, conversation timeline, product interests
- **Thread Tracking**: View complete email conversation history
- **Status Badges**: Visual indicators for priority, status, duplicates
- **Stats Dashboard**: Total, new, responded, customer replied, avg quality

### 📚 Knowledge Base Page (`/knowledge`)
- **Document Management**: View, upload, and deactivate knowledge base documents
- **Stats Overview**: Total documents, chunks, document type breakdown
- **RAG Query Tester**: Test semantic search with similarity scores
- **Re-index Control**: Trigger full knowledge base re-indexing
- **Document Details**: Chunk counts, versions, last updated timestamps
- **Type Filtering**: Documents organized by type (FAQ, process, pricing, capability)

### 🏠 Dashboard Page (`/`)
- **Overview Metrics**: Total leads, pending drafts, avg response time
- **Recent Leads**: Last 5 leads with quality scores and priorities
- **Pending Drafts**: Quick access to drafts needing review
- **System Status**: RAG system, AI agents, email service health

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Email IMAP/SMTP credentials
- OpenRouter API key (https://openrouter.ai/)

### Installation

1. **Clone the repository:**
```bash
cd /var/www/emailagent
```

2. **Configure environment:**
```bash
cp .env.example .env
```

3. **Edit `.env` with your credentials:**
```bash
# Email Configuration
EMAIL_ADDRESS=your-email@nutricraftlabs.com
EMAIL_PASSWORD=your-email-password
EMAIL_IMAP_HOST=your-imap-host
EMAIL_SMTP_HOST=your-smtp-host

# OpenRouter API (Required)
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_EXTRACTION_MODEL=anthropic/claude-haiku-4.5
OPENROUTER_RESPONSE_MODEL=anthropic/claude-sonnet-4.5

# Model Settings
LLM_TEMPERATURE_EXTRACTION=0.3
LLM_TEMPERATURE_RESPONSE=0.7
LLM_MAX_TOKENS=4000
LLM_TIMEOUT=60
```

4. **Start all services:**
```bash
docker compose up -d
```

5. **Access the application:**
- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/api/docs

### Testing the System

Run the integration test suite:
```bash
docker compose exec backend python3 /app/test_integration.py
```

Expected output:
```
✅ Extraction Agent      PASSED
✅ Response Agent        PASSED
✅ Full Pipeline         PASSED
✅ Analytics Agent       PASSED
```

## Project Structure

```
emailagent/
├── backend/                      # FastAPI backend
│   ├── agents/                   # PydanticAI agents
│   │   ├── extraction_agent.py   # Lead data extraction
│   │   ├── response_agent.py     # Email response generation
│   │   └── analytics_agent.py    # Pure Python analytics
│   ├── models/
│   │   ├── agent_responses.py    # Pydantic output models
│   │   ├── agent_dependencies.py # Dependency injection models
│   │   ├── database.py           # SQLAlchemy models
│   │   └── schemas.py            # API schemas
│   ├── services/
│   │   └── pydantic_ai_client.py # OpenRouter configuration
│   ├── rag/                      # RAG system
│   │   └── semantic_search.py    # Vector search
│   ├── api/                      # API endpoints
│   ├── tasks/                    # Celery background tasks
│   └── test_integration.py       # Integration tests
├── frontend/                     # React dashboard
│   └── src/
│       ├── components/           # React components
│       ├── pages/                # Dashboard pages
│       └── services/             # API client
├── knowledge/                    # Knowledge base documents
│   ├── products/                 # Product catalogs
│   ├── pricing/                  # Pricing guides
│   ├── certifications/           # Certification info
│   └── faq/                      # FAQs
├── planning/                     # Project documentation
│   ├── PRD.md                    # Product requirements
│   └── pydanticai_task.md        # PydanticAI task list
├── scripts/                      # Utility scripts
└── PYDANTICAI_IMPLEMENTATION_SUMMARY.md  # Implementation details
```

## Ports

- **Frontend**: 3001 (external) → 3000 (internal)
- **Backend**: 8001 (external) → 8000 (internal)
- **PostgreSQL**: 5434 (external) → 5432 (internal)
- **Redis**: 6380 (external) → 6379 (internal)
- **pgAdmin**: 5050 (optional, use `--profile tools`)

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Testing PydanticAI Agents
```bash
# Run integration tests
docker compose exec backend python3 /app/test_integration.py

# Test extraction agent
docker compose exec backend python3 -c "
from agents.extraction_agent import get_extraction_agent
import asyncio

async def test():
    agent = get_extraction_agent()
    result = await agent.extract_from_email({
        'sender_email': 'test@example.com',
        'sender_name': 'Test User',
        'subject': 'Probiotic Inquiry',
        'body': 'Looking for probiotic manufacturing...'
    })
    print(result)

asyncio.run(test())
"
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Configuration

### Environment Variables

#### Required
- `OPENROUTER_API_KEY` - OpenRouter API key (get from https://openrouter.ai/)
- `EMAIL_ADDRESS` - Email address to monitor
- `EMAIL_PASSWORD` - Email password
- `EMAIL_IMAP_HOST` - IMAP server hostname
- `EMAIL_SMTP_HOST` - SMTP server hostname
- `DB_PASSWORD` - Database password

#### Optional (with defaults)
- `OPENROUTER_EXTRACTION_MODEL` - Default: `anthropic/claude-haiku-4.5`
- `OPENROUTER_RESPONSE_MODEL` - Default: `anthropic/claude-sonnet-4.5`
- `LLM_TEMPERATURE_EXTRACTION` - Default: `0.3`
- `LLM_TEMPERATURE_RESPONSE` - Default: `0.7`
- `LLM_MAX_TOKENS` - Default: `4000`
- `LLM_TIMEOUT` - Default: `60`

### Model Selection

The system is configured to use different models for different tasks:

| Task | Model | Purpose | Temperature |
|------|-------|---------|-------------|
| Extraction | Claude 4.5 Haiku | Fast, cheap extraction | 0.3 (precise) |
| Response | Claude 4.5 Sonnet | High-quality writing | 0.7 (natural) |

You can change models by updating the `.env` file and restarting services.

## Monitoring

### Logs
```bash
# View all logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# View celery worker logs
docker compose logs -f celery-worker
```

### Health Check
```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development",
  "database": "connected",
  "timestamp": "2025-10-22T..."
}
```

## Documentation

- [PydanticAI Implementation Summary](PYDANTICAI_IMPLEMENTATION_SUMMARY.md) - Complete implementation details
- [Thread Tracking Implementation](THREAD_TRACKING_IMPLEMENTATION.md) - Email threading and duplicate detection
- [Product Requirements Document (PRD)](planning/PRD.md) - Product requirements
- [PydanticAI Task List](planning/pydanticai_task.md) - Implementation phases
- [API Documentation](http://localhost:8001/api/docs) - Interactive API docs (when running)

## Recent Updates

### Version 2.2.0 (October 2025)
- ✅ **Complete Frontend Dashboard**: All pages fully implemented
- ✅ **Analytics Page**: Interactive charts with Recharts (pie, bar, line charts)
- ✅ **Leads Browser**: Advanced search, filters, sorting, conversation timeline viewer
- ✅ **Knowledge Base Management**: Document viewer, upload UI, RAG query tester
- ✅ **Email Thread Tracking**: Conversation threading, duplicate detection, reply classification
- ✅ **CORS Configuration**: Network IP support for LAN access
- ✅ **Database Relationships**: Lead-Draft relationships with eager loading
- ✅ **Conversation API**: Full timeline view with all email interactions

### Version 2.1.0 (October 2025)
- ✅ **PydanticAI Integration**: Complete migration to PydanticAI framework
- ✅ **OpenRouter Support**: Flexible LLM provider integration
- ✅ **Type Safety**: All agent outputs validated by Pydantic models
- ✅ **Dynamic Prompts**: System prompts adapt based on lead priority
- ✅ **RAG Tools**: Custom tools for knowledge base integration
- ✅ **Automatic Retries**: Built-in retry mechanism on validation failure
- ✅ **Fallback Systems**: Graceful degradation for reliability
- ✅ **100% Backward Compatible**: No breaking changes to existing APIs

## Performance & Cost

### Model Costs (OpenRouter)
- **Extraction** (Haiku): ~$0.25 per 1M input tokens
- **Response** (Sonnet): ~$3.00 per 1M input tokens

### Typical Email Processing
- **Extraction**: ~500 tokens = $0.000125
- **Response**: ~1500 tokens = $0.0045
- **Total per email**: ~$0.005 (half a cent)

### Processing Speed
- **Extraction**: 1-3 seconds
- **Response Generation**: 3-7 seconds
- **Total Pipeline**: 5-10 seconds

## Troubleshooting

### Agent not working
```bash
# Check configuration
docker compose exec backend python3 -c "from config import get_settings; s = get_settings(); print(f'API Key: {s.OPENROUTER_API_KEY[:20]}...')"

# Restart services
docker compose restart backend celery-worker
```

### Database connection issues
```bash
# Check database
docker compose exec postgres psql -U emailagent_user -d supplement_leads_db -c "SELECT 1;"
```

### Knowledge base not working
```bash
# Check documents
docker compose exec backend python3 -c "from rag import get_semantic_search; import asyncio; asyncio.run(get_semantic_search().get_document_count())"
```

## License

Proprietary - Nutricraft Labs

## Support

For issues and questions:
1. Check logs: `docker compose logs -f backend`
2. Run tests: `docker compose exec backend python3 /app/test_integration.py`
3. Review documentation: [PYDANTICAI_IMPLEMENTATION_SUMMARY.md](PYDANTICAI_IMPLEMENTATION_SUMMARY.md)
4. Contact the development team

---

**Built with ❤️ using PydanticAI, FastAPI, and React**
