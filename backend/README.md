# Backend - Supplement Lead Intelligence System

FastAPI backend with multi-agent AI system and RAG capabilities.

## Structure

- `agents/` - AI agents (extraction, response, analytics)
- `rag/` - RAG system (document processing, embeddings, retrieval)
- `services/` - Business logic services
- `api/` - FastAPI route handlers
- `models/` - Database models and Pydantic schemas
- `tasks/` - Celery background tasks

## Running

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testing

```bash
pytest
```
