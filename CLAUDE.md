# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a supplement manufacturing lead intelligence system built with FastAPI (backend), React (frontend), and **PydanticAI** for type-safe AI agents. The system monitors email inboxes, extracts structured lead data using LLMs, generates RAG-enhanced draft responses, and provides analytics on product trends.

**Key Architecture:** Multi-agent system using PydanticAI with OpenRouter (Claude 4.5 models) for extraction and response generation, with PostgreSQL+pgvector for RAG semantic search.

## Development Commands

### Docker Environment (Primary)
```bash
# Start all services
docker compose up -d

# Rebuild after dependency changes
docker compose build --no-cache backend
docker compose restart backend celery-worker celery-beat

# View logs
docker compose logs -f backend
docker compose logs -f celery-worker

# Run integration tests
docker compose exec backend python3 /app/test_integration.py

# Access backend shell
docker compose exec backend bash

# Database migrations
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Backend Development
```bash
# Run locally (outside Docker)
cd backend
uvicorn main:app --reload --port 8000

# Run single test file
pytest tests/test_agents.py -v

# Ingest knowledge base documents
docker compose exec backend python3 scripts/ingest_knowledge_base.py
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

## Architecture Overview

### PydanticAI Agent System

The core innovation is the **type-safe AI agent system** using PydanticAI:

1. **Extraction Agent** (`backend/agents/extraction_agent.py`)
   - Uses Claude 4.5 Haiku (fast/cheap)
   - Output type: `LeadExtraction` Pydantic model (automatic validation)
   - Tools: `search_knowledge_base()`, `validate_product_type()`
   - Output validator ensures data quality (lead score 1-10, valid priorities)
   - Fallback to keyword extraction on API failures

2. **Response Agent** (`backend/agents/response_agent.py`)
   - Uses Claude 4.5 Sonnet (high quality)
   - Output type: `ResponseDraft` Pydantic model
   - **Dynamic system prompts** based on lead priority (critical/high/medium/low)
   - Tools: `search_knowledge_base()`, `get_comprehensive_context()`
   - Output validator checks email format (greeting, signature, length)
   - Fallback to template responses on API failures

3. **Analytics Agent** (`backend/agents/analytics_agent.py`)
   - Pure Python, no LLM (cost optimization)
   - Tracks product trends, lead quality metrics

**Key Pattern:** All agents return Pydantic models that are converted to dicts via `result.output.model_dump()` for backward compatibility with existing APIs.

### Agent Configuration

Located in `backend/services/pydantic_ai_client.py`:
- OpenRouter provider setup
- Model selection (extraction vs response)
- Temperature settings (0.3 for extraction, 0.7 for response)
- Timeout and token limits

**Critical:** Agents are initialized at module load time. Changes require container restart.

### RAG System Architecture

Located in `backend/rag/`:

1. **Document Processing** (`document_processor.py`)
   - Ingests PDF, Markdown from `knowledge/` directory
   - Chunks documents semantically (markdown sections, PDF paragraphs)
   - Generates embeddings via OpenAI API (fallback: sentence-transformers)

2. **Semantic Search** (`semantic_search.py`)
   - PostgreSQL pgvector for vector similarity search
   - `similarity_search()`: Returns top-k chunks above threshold
   - `get_context_for_query()`: Formats chunks for LLM context
   - Used by agent tools to retrieve relevant knowledge

3. **Embeddings** (`embeddings.py`)
   - Primary: OpenAI `text-embedding-3-small`
   - Fallback: `all-MiniLM-L6-v2` (local, no API needed)

**Knowledge Base Flow:**
```
knowledge/*.md → ingest_knowledge_base.py → document_embeddings table →
pgvector search → agent RAG tools → LLM context
```

### Historical Response Learning System

The system can backfill historical emails to learn from your actual manual responses, improving AI-generated drafts.

**Architecture:**

1. **Historical Backfill** (`backend/services/historical_backfill.py`)
   - IMAP server-side filtering (only fetches emails matching subject pattern)
   - Searches both INBOX and Sent folders simultaneously
   - Matches responses to inquiries using email threading (In-Reply-To/References)
   - Fallback matching: Time-based (90-day window) + subject similarity
   - Stores matched pairs with `is_historical=True` flag

2. **Response Learning** (`backend/services/response_learning.py`)
   - Analyzes historical responses to extract writing style patterns
   - Metrics tracked: length, structure, tone, vocabulary, CTAs
   - Generates enhanced system prompts with learned patterns
   - Example patterns: avg word count, greeting style, common phrases

3. **Historical Response RAG** (`backend/rag/historical_response_retrieval.py`)
   - Semantic search for similar past inquiries using pgvector
   - Returns top-k similar examples with your actual responses
   - Used by Response Agent's `get_similar_past_responses()` tool
   - AI adapts tone and style from retrieved examples

**Database Schema:**
- `historical_response_examples` table: Stores responses with embeddings
- `leads` table extensions: `is_historical`, `human_response_body`, `human_response_date`

**API Endpoints** (`backend/api/backfill.py`):
```bash
POST /api/backfill/start              # Trigger backfill
GET  /api/backfill/status/{task_id}   # Check progress
GET  /api/backfill/summary            # View results
GET  /api/backfill/historical-responses  # Browse stored responses
POST /api/backfill/analyze-patterns   # Re-analyze writing style
GET  /api/backfill/test-connection    # Test inbox credentials
```

**Configuration** (optional, in `.env`):
```bash
HISTORICAL_EMAIL_ADDRESS=your.email@domain.com
HISTORICAL_EMAIL_PASSWORD=...
HISTORICAL_IMAP_HOST=imap.domain.com
HISTORICAL_IMAP_PORT=993
BACKFILL_SUBJECT_FILTER="Contact Form: "
BACKFILL_LOOKBACK_DAYS=365
```

**Usage Example:**
```bash
# Run backfill (one-time setup)
curl -X POST http://localhost:8001/api/backfill/start \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'

# Check results
curl http://localhost:8001/api/backfill/summary
```

**Response Agent Enhancement:**
- New tool: `get_similar_past_responses()` retrieves historical examples
- System prompts enhanced with learned writing patterns
- AI automatically adapts to your response style

### Database Models

Two separate model systems (don't confuse them):

1. **SQLAlchemy ORM Models** (`backend/models/database.py`)
   - `Lead`: Extracted email data (JSONB fields for arrays)
     - Extensions: `is_historical`, `source_type`, `human_response_body`, `human_response_date`
   - `Draft`: Generated response drafts
   - `DocumentEmbedding`: RAG vector store (pgvector)
   - `HistoricalResponseExample`: Stored historical responses with embeddings for AI learning
   - `ProductTypeTrend`: Analytics tracking
   - `AnalyticsSnapshot`: Daily metrics
   - `Conversation`: Email thread tracking
   - `EmailMessage`: Individual email messages (inbound/outbound)

2. **Pydantic Models** (`backend/models/`)
   - `agent_responses.py`: LLM output schemas (LeadExtraction, ResponseDraft)
   - `agent_dependencies.py`: Dependency injection for agents
   - `schemas.py`: API request/response schemas

**Key Difference:** Pydantic models validate LLM outputs; SQLAlchemy models persist to database.

### Background Tasks (Celery)

Located in `backend/tasks/`:

1. **Email Tasks** (`email_tasks.py`)
   - `check_and_process_emails`: Polls IMAP every 5 minutes
   - `process_single_email`: Pipeline: fetch → extract → generate draft → save

2. **Analytics Tasks** (`analytics_tasks.py`)
   - `generate_daily_analytics`: Runs at midnight
   - `update_product_trends`: Tracks mentions over time

**Celery Configuration:**
- Broker: Redis
- Beat schedule in `celery_app.py`
- Worker: `celery-worker` container (concurrency=2)
- Beat: `celery-beat` container (scheduler)

### API Structure

RESTful endpoints in `backend/api/`:
- `/api/leads`: CRUD for extracted leads
- `/api/drafts`: CRUD for draft responses, approval workflow
- `/api/analytics`: Metrics, trends, snapshots
- `/api/knowledge`: Knowledge base document management
- `/api/backfill`: Historical email backfill and response learning
- `/api/conversations`: Email conversation threads

All routes use async SQLAlchemy sessions via `Depends(get_db)`.

## Critical Configuration

### Environment Variables

Must be set in `.env` (see `.env.example`):

```bash
# REQUIRED for agents to work
OPENROUTER_API_KEY=sk-or-v1-...

# Model selection (defaults in config.py)
OPENROUTER_EXTRACTION_MODEL=anthropic/claude-haiku-4.5
OPENROUTER_RESPONSE_MODEL=anthropic/claude-sonnet-4.5

# Email monitoring
EMAIL_ADDRESS=contact@yourdomain.com
EMAIL_PASSWORD=...
EMAIL_IMAP_HOST=imap.yourdomain.com
EMAIL_SMTP_HOST=smtp.yourdomain.com

# Database
DATABASE_URL=postgresql://...
```

**Docker Compose:** Environment variables must be explicitly passed in `docker-compose.yml` to each service (backend, celery-worker, celery-beat).

### Agent Temperature Settings

- **Extraction**: `LLM_TEMPERATURE_EXTRACTION=0.3` (lower = more deterministic)
- **Response**: `LLM_TEMPERATURE_RESPONSE=0.7` (higher = more natural/creative)

These are passed to `ModelSettings` in `pydantic_ai_client.py`.

## Testing

### Integration Tests

Run the comprehensive test suite:
```bash
docker compose exec backend python3 /app/test_integration.py
```

Tests verify:
- Extraction agent with real/mock LLM calls
- Response agent with dynamic prompts
- Full pipeline (email → extraction → response)
- Fallback mechanisms

**Expected output:**
```
✅ Extraction Agent      PASSED
✅ Response Agent        PASSED
✅ Full Pipeline         PASSED
✅ Analytics Agent       PASSED
```

### Manual Agent Testing

Test extraction agent:
```python
from agents.extraction_agent import get_extraction_agent
import asyncio

async def test():
    agent = get_extraction_agent()
    result = await agent.extract_from_email({
        'sender_email': 'test@example.com',
        'subject': 'Probiotic Inquiry',
        'body': 'Looking for probiotic manufacturing...',
        'message_id': 'test-001'
    })
    print(result)

asyncio.run(test())
```

## Common Patterns

### Adding a New Agent Tool

Tools are methods decorated with `@agent.tool`:

```python
@extraction_agent.tool
async def my_new_tool(ctx: RunContext[ExtractionDeps], query: str) -> str:
    """Tool description for the LLM"""
    # Access dependencies via ctx.deps.config, ctx.deps.email_data
    # Return string result that LLM can use
    return "result"
```

Tools have access to:
- `ctx.deps.config`: Application settings
- `ctx.deps.email_data` (extraction) or `ctx.deps.lead_data` (response)
- Async functions (can call database, external APIs)

### Adding Output Validators

Validators run after LLM generates output:

```python
@extraction_agent.output_validator
async def validate_extraction(ctx: RunContext[ExtractionDeps], result: LeadExtraction) -> LeadExtraction:
    if result.lead_quality_score < 1 or result.lead_quality_score > 10:
        raise ModelRetry("Score must be 1-10")  # Triggers retry
    return result
```

**ModelRetry exception:** Causes PydanticAI to retry (up to `retries=2` attempts).

### Modifying Agent System Prompts

For static prompts, edit the `system_prompt` parameter in agent initialization.

For dynamic prompts (like response agent), modify `get_dynamic_system_prompt()` function and update the system prompt at runtime:

```python
response_agent._system_prompts = [get_dynamic_system_prompt(priority)]
```

### Accessing PydanticAI Results

**Correct:** `result.output.model_dump()`
**Incorrect:** `result.data.model_dump()` (old API, removed)

The `.output` attribute contains the validated Pydantic model.

## Troubleshooting

### Agents Return Fallback Responses

Causes:
1. `OPENROUTER_API_KEY` not set or invalid
2. Model name incorrect (must match OpenRouter catalog)
3. API rate limit or timeout

Check configuration:
```bash
docker compose exec backend python3 -c "from config import get_settings; s = get_settings(); print(s.OPENROUTER_API_KEY[:20])"
```

### Knowledge Base Search Returns No Results

1. Verify documents are ingested:
```bash
docker compose exec backend python3 -c "from rag import get_semantic_search; import asyncio; print(asyncio.run(get_semantic_search().get_document_count()))"
```

2. Re-ingest if needed:
```bash
docker compose exec backend python3 scripts/ingest_knowledge_base.py
```

### Celery Tasks Not Running

Check worker and beat are running:
```bash
docker compose logs celery-worker
docker compose logs celery-beat
```

Tasks are scheduled in `backend/tasks/celery_app.py` beat_schedule dict.

## Important Notes

- **Container Restart Required:** Agent initialization happens at module import. Any changes to agent code, models, or configuration require `docker compose restart backend celery-worker`.

- **Backward Compatibility:** Agent wrappers (`ExtractionAgentWrapper`, `ResponseAgentWrapper`) maintain dict-based interfaces for existing code. Internal agent calls use Pydantic models.

- **RAG Context Length:** Default max_tokens for RAG context is 3000. Adjust in `get_context_for_query()` calls if needed.

- **Database Schema:** Uses JSONB for array fields (product_type, certifications). Query with `.contains()` for filtering.

- **Email Polling:** Default interval is 5 minutes (Celery beat schedule). Adjust in `celery_app.py` if needed.

- **Error Handling:** All agents have fallback mechanisms. Check logs for "Using fallback extraction" or "Using fallback response" warnings.
