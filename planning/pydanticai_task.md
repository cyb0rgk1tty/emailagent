# PydanticAI Refactoring Implementation Task List

## Overview

This task list outlines the complete refactoring of the Supplement Lead Intelligence System to use **PydanticAI** with **OpenRouter** as the LLM provider. PydanticAI is the optimal choice for this project due to its native Pydantic integration, type-safe structured outputs, and agent-based architecture that perfectly matches our multi-agent design.

**Official Documentation**: https://ai.pydantic.dev/

### 📌 Simplified Approach
This implementation uses **custom PydanticAI tools only** (not MCP servers):
- ✅ **Simpler**: No external server configuration
- ✅ **Faster**: Direct Python function calls
- ✅ **Practical**: All our tools are internal (RAG, validation)
- ✅ **Easier**: Better testing, debugging, and maintenance

**MCP Support**: PydanticAI has MCP support, but we don't need it for this project. Consider MCP later if you add external integrations (market research, CRM, etc.)

---

## Why PydanticAI for This Project?

### ✅ Perfect Fit Reasons:
1. **Native Structured Outputs**: Our extraction agent needs JSON - PydanticAI handles this with Pydantic models
2. **Multi-Agent Architecture**: Built for our 3-agent system (Extraction, Response, Analytics)
3. **Type Safety**: Full type checking with existing Pydantic models
4. **OpenRouter Compatible**: Direct support via OpenAI-compatible API
5. **Custom Tool Support**: Simple Python functions for RAG and validation
6. **Dependency Injection**: Clean way to pass DB sessions, config, RAG
7. **FastAPI Ecosystem**: Same team, familiar patterns
8. **Modern Python**: Async/await, type hints, Pydantic v2

### 🎯 Simplified Approach (No MCP):
- **Using**: Custom PydanticAI tools (Python functions)
- **Not Using**: MCP servers (unnecessary for internal tools)
- **Reason**: All our tools are internal (RAG, DB, config validation)
- **Benefit**: Simpler, faster, easier to test and debug

### 📊 Architecture Overview:

```
┌─────────────────────────────────────────────────────────────┐
│                    EMAIL PROCESSING PIPELINE                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Email → [Extraction Agent] → Lead Data → [Response Agent]  │
│              ↓                                  ↓             │
│          RAG Tools                          RAG Tools         │
│              ↓                                  ↓             │
│         PostgreSQL                        Draft Response     │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Agent Details:
- Extraction Agent: PydanticAI with structured output
- Response Agent: PydanticAI with RAG tools
- Analytics Agent: Pure Python/SQL (no LLM needed)
```

---

## Phase 1: Foundation & Configuration

### Task 1.1: Install PydanticAI Dependencies
**File**: `backend/requirements.txt`

**Actions**:
- Add `pydantic-ai-slim[openai]==1.0.5` (latest stable version)
- Verify compatibility with existing `pydantic==2.5.3`
- Add `httpx==0.26.0` (already present, but verify version for PydanticAI)
- **Note**: We're using `[openai]` not `[mcp]` - we don't need MCP for internal tools

**Dependencies Added**:
```txt
# AI Framework
pydantic-ai-slim[openai]==1.0.5  # Agent framework with OpenAI-compatible API support

# Already present:
anthropic==0.18.1  # For OpenRouter compatibility
openai==1.12.0     # OpenAI SDK (used by PydanticAI)
httpx==0.26.0      # HTTP client for API calls
```

**Why NOT `[mcp]`?**
- We only need internal custom tools (RAG, validation)
- No external MCP servers required
- Simpler, faster, fewer dependencies

**Verification**:
```bash
docker compose build backend
docker compose run --rm backend python -c "import pydantic_ai; print(pydantic_ai.__version__)"
```

---

### Task 1.2: Configure OpenRouter Settings
**Files**:
- `backend/config.py`
- `.env`
- `.env.example`

**Actions in `config.py`**:
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # AI Configuration - OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"  # Default model
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Alternative models for different use cases
    OPENROUTER_EXTRACTION_MODEL: str = "anthropic/claude-3.5-sonnet"  # Structured output
    OPENROUTER_RESPONSE_MODEL: str = "anthropic/claude-3.5-sonnet"     # Text generation

    # Model settings
    LLM_TEMPERATURE_EXTRACTION: float = 0.3  # Low for consistent extraction
    LLM_TEMPERATURE_RESPONSE: float = 0.7    # Higher for natural writing
    LLM_MAX_TOKENS: int = 4000
    LLM_TIMEOUT: int = 60  # seconds

    # Remove old fields (deprecated):
    # USE_CLAUDE_CODE_SESSION: bool = True  # DELETE
    # ANTHROPIC_API_KEY: str = ""           # DELETE (using OpenRouter instead)
```

**Actions in `.env`**:
```env
# AI Configuration - OpenRouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_EXTRACTION_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_RESPONSE_MODEL=anthropic/claude-3.5-sonnet

# Model Settings
LLM_TEMPERATURE_EXTRACTION=0.3
LLM_TEMPERATURE_RESPONSE=0.7
LLM_MAX_TOKENS=4000
LLM_TIMEOUT=60
```

**Actions in `.env.example`**:
- Update with same OpenRouter configuration
- Remove deprecated Claude Code session references
- Add comments with OpenRouter signup link: https://openrouter.ai/

**Verification**:
```python
from config import get_settings
settings = get_settings()
assert settings.OPENROUTER_API_KEY
assert settings.OPENROUTER_MODEL
```

---

### Task 1.3: Create PydanticAI Client Service
**File**: `backend/services/pydantic_ai_client.py` (NEW FILE)

**Purpose**: Centralized model configuration for all agents

**Implementation**:
```python
"""
PydanticAI client configuration for OpenRouter
Provides configured models for all agents
"""
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from config import get_settings
import httpx

settings = get_settings()


def get_extraction_model() -> OpenAIChatModel:
    """Get configured model for extraction agent (structured output)

    Returns:
        OpenAIChatModel configured for OpenRouter
    """
    return OpenAIChatModel(
        model_name=settings.OPENROUTER_EXTRACTION_MODEL,
        provider=OpenRouterProvider(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            http_client=httpx.AsyncClient(
                timeout=settings.LLM_TIMEOUT,
                headers={
                    "HTTP-Referer": "https://nutricraftlabs.com",  # Optional
                    "X-Title": "Nutricraft Supplement Lead System"
                }
            )
        ),
        temperature=settings.LLM_TEMPERATURE_EXTRACTION,
        max_tokens=settings.LLM_MAX_TOKENS,
    )


def get_response_model() -> OpenAIChatModel:
    """Get configured model for response agent (text generation)

    Returns:
        OpenAIChatModel configured for OpenRouter
    """
    return OpenAIChatModel(
        model_name=settings.OPENROUTER_RESPONSE_MODEL,
        provider=OpenRouterProvider(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            http_client=httpx.AsyncClient(
                timeout=settings.LLM_TIMEOUT,
                headers={
                    "HTTP-Referer": "https://nutricraftlabs.com",
                    "X-Title": "Nutricraft Supplement Lead System"
                }
            )
        ),
        temperature=settings.LLM_TEMPERATURE_RESPONSE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )


def get_model(model_type: str = "extraction") -> OpenAIChatModel:
    """Get model by type

    Args:
        model_type: "extraction" or "response"

    Returns:
        Configured OpenAIChatModel
    """
    if model_type == "extraction":
        return get_extraction_model()
    elif model_type == "response":
        return get_response_model()
    else:
        raise ValueError(f"Unknown model type: {model_type}")
```

**Verification**:
```python
from services.pydantic_ai_client import get_extraction_model, get_response_model
model1 = get_extraction_model()
model2 = get_response_model()
assert model1.model_name == "anthropic/claude-3.5-sonnet"
```

---

## Phase 2: Define Pydantic Response Models

### Task 2.1: Create Agent Response Models
**File**: `backend/models/agent_responses.py` (NEW FILE)

**Purpose**: Type-safe Pydantic models for agent outputs

**Implementation**:
```python
"""
Pydantic models for AI agent structured outputs
Used by PydanticAI agents to enforce type-safe responses
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class LeadExtraction(BaseModel):
    """Structured output from extraction agent"""

    # Product Information
    product_type: list[str] = Field(
        default_factory=list,
        description="Array of product types mentioned (probiotics, electrolytes, etc.)"
    )
    specific_ingredients: Optional[list[str]] = Field(
        default=None,
        description="Specific ingredients or compounds mentioned"
    )
    delivery_format: Optional[list[str]] = Field(
        default=None,
        description="Delivery formats (capsule, powder, gummy, etc.)"
    )
    certifications_requested: Optional[list[str]] = Field(
        default=None,
        description="Certifications requested (organic, non-gmo, vegan, etc.)"
    )

    # Business Intelligence
    estimated_quantity: Optional[str] = Field(
        default=None,
        description="Quantity mentioned (e.g., '5000 units', '10,000-25,000')"
    )
    timeline_urgency: Optional[str] = Field(
        default="exploring",
        description="Timeline urgency: urgent, medium-1-3-months, long-term-6-plus-months, exploring"
    )
    budget_indicator: Optional[str] = Field(
        default=None,
        description="Budget level: startup, mid-market, enterprise"
    )
    experience_level: Optional[str] = Field(
        default=None,
        description="Experience: first-time, established-brand, experienced"
    )
    distribution_channel: Optional[list[str]] = Field(
        default=None,
        description="Distribution channels (e-commerce, retail, amazon, subscription)"
    )
    has_existing_brand: Optional[bool] = Field(
        default=None,
        description="Whether they have an existing brand"
    )

    # Additional Context
    specific_questions: Optional[list[str]] = Field(
        default=None,
        description="Specific questions they asked"
    )
    geographic_region: Optional[str] = Field(
        default=None,
        description="Geographic region if mentioned (US, Canada, UK, etc.)"
    )

    # Lead Scoring
    lead_quality_score: int = Field(
        ge=1,
        le=10,
        description="Lead quality score 1-10 based on detail, budget, urgency, specificity"
    )
    response_priority: str = Field(
        description="Priority: critical, high, medium, low"
    )
    extraction_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in extraction accuracy (0-1)"
    )

    @field_validator('response_priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid = ['critical', 'high', 'medium', 'low']
        if v not in valid:
            raise ValueError(f"Priority must be one of {valid}")
        return v

    @field_validator('timeline_urgency')
    @classmethod
    def validate_timeline(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = ['urgent', 'medium-1-3-months', 'long-term-6-plus-months', 'exploring']
        if v not in valid:
            raise ValueError(f"Timeline must be one of {valid}")
        return v


class ResponseDraft(BaseModel):
    """Structured output from response agent"""

    subject_line: str = Field(
        description="Email subject line (Re: original subject)"
    )
    draft_content: str = Field(
        description="Full email draft content"
    )
    response_type: str = Field(
        description="Response type: high_priority_detailed, detailed_quote, standard_inquiry, basic_information"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=10.0,
        description="Confidence in draft quality (0-10)"
    )
    flags: list[str] = Field(
        default_factory=list,
        description="Flags: limited_knowledge_base_match, low_quality_lead, unclear_product_needs, etc."
    )
    rag_sources: list[str] = Field(
        default_factory=list,
        description="Knowledge base sources used"
    )
    status: str = Field(
        default="pending",
        description="Draft status: pending, approved, rejected, sent, edited"
    )

    @field_validator('response_type')
    @classmethod
    def validate_response_type(cls, v: str) -> str:
        valid = ['high_priority_detailed', 'detailed_quote', 'standard_inquiry', 'basic_information', 'fallback']
        if v not in valid:
            raise ValueError(f"Response type must be one of {valid}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = ['pending', 'approved', 'rejected', 'sent', 'edited']
        if v not in valid:
            raise ValueError(f"Status must be one of {valid}")
        return v


class AnalyticsInsight(BaseModel):
    """Structured output for analytics insights (if needed for LLM-based insights)"""

    insight_type: str = Field(
        description="Type: trend, anomaly, recommendation"
    )
    title: str = Field(
        description="Short insight title"
    )
    description: str = Field(
        description="Detailed insight description"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in insight"
    )
    action_items: Optional[list[str]] = Field(
        default=None,
        description="Recommended actions"
    )
```

**Verification**:
```python
from models.agent_responses import LeadExtraction, ResponseDraft

# Test validation
lead = LeadExtraction(
    product_type=["probiotics"],
    lead_quality_score=8,
    response_priority="high",
    extraction_confidence=0.85
)
assert lead.lead_quality_score == 8

# Test validation failure
try:
    bad_lead = LeadExtraction(
        product_type=[],
        lead_quality_score=15,  # Invalid!
        response_priority="high",
        extraction_confidence=0.85
    )
except ValueError:
    print("✅ Validation working")
```

---

### Task 2.2: Create Agent Dependencies Models
**File**: `backend/models/agent_dependencies.py` (NEW FILE)

**Purpose**: Type-safe dependency injection for agents

**Implementation**:
```python
"""
Dependency models for PydanticAI agents
Used for dependency injection into agent tools and validators
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from config import Settings


@dataclass
class BaseDeps:
    """Base dependencies for all agents"""
    config: Settings

    class Config:
        arbitrary_types_allowed = True


@dataclass
class ExtractionDeps(BaseDeps):
    """Dependencies for extraction agent

    Attributes:
        config: Application settings
        email_data: Original email data for reference
    """
    email_data: Dict[str, Any]


@dataclass
class ResponseDeps(BaseDeps):
    """Dependencies for response agent

    Attributes:
        config: Application settings
        lead_data: Extracted lead data
        email_content: Original email content
    """
    lead_data: Dict[str, Any]
    email_content: str


@dataclass
class AnalyticsDeps(BaseDeps):
    """Dependencies for analytics agent (if LLM-based insights needed)

    Attributes:
        config: Application settings
        db: Database session
        timeframe: Analysis timeframe
    """
    db: AsyncSession
    timeframe: str = "30d"

    class Config:
        arbitrary_types_allowed = True
```

---

## Phase 3: Refactor Extraction Agent

### Task 3.1: Refactor Extraction Agent to PydanticAI
**File**: `backend/agents/extraction_agent.py`

**Strategy**:
1. Replace `ClaudeAgent()` with PydanticAI `Agent`
2. Convert prompts to `system_prompt` + `instructions`
3. Add RAG tools for product/certification validation
4. Use `LeadExtraction` as `output_type`
5. Add output validators for quality checks

**Key Changes**:
```python
"""
Extraction Agent - Extracts structured data from lead emails
Uses PydanticAI with OpenRouter for intelligent field extraction
"""
import logging
from typing import Dict, Optional
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIChatModel

from models.agent_responses import LeadExtraction
from models.agent_dependencies import ExtractionDeps
from services.pydantic_ai_client import get_extraction_model
from rag import get_semantic_search
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Initialize PydanticAI agent
extraction_agent = Agent[ExtractionDeps, LeadExtraction](
    model=get_extraction_model(),
    output_type=LeadExtraction,
    deps_type=ExtractionDeps,
    system_prompt="""You are an expert supplement industry business intelligence analyst.
Your role is to analyze lead emails and extract structured data about supplement manufacturing needs.

Extract product types, certifications, delivery formats, business intelligence, and lead quality.
Be precise and conservative - only extract data that is explicitly mentioned.
Use the search_knowledge_base tool to validate product types and certifications.""",
    retries=2,  # Retry up to 2 times on validation failure
)


@extraction_agent.tool
async def search_knowledge_base(ctx: RunContext[ExtractionDeps], query: str) -> str:
    """Search the knowledge base for product types, certifications, or capabilities

    Args:
        query: Search query (e.g., "probiotics certification requirements")

    Returns:
        Relevant context from knowledge base
    """
    try:
        semantic_search = get_semantic_search()
        results = await semantic_search.similarity_search(
            query=query,
            top_k=3,
            min_similarity=0.5
        )

        if not results:
            return "No relevant information found in knowledge base."

        # Format results
        formatted = []
        for r in results:
            formatted.append(
                f"Source: {r['document_name']}\n"
                f"Content: {r['text'][:200]}...\n"
                f"Similarity: {r['similarity']:.2f}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return f"Error searching knowledge base: {str(e)}"


@extraction_agent.tool
async def validate_product_type(ctx: RunContext[ExtractionDeps], product_type: str) -> str:
    """Validate if a product type is supported

    Args:
        product_type: Product type to validate

    Returns:
        Validation result
    """
    valid_types = ctx.deps.config.PRODUCT_TYPES

    product_lower = product_type.lower().replace(' ', '-')

    if product_lower in valid_types:
        return f"✓ '{product_type}' is a valid product type"

    # Check for close matches
    close_matches = [pt for pt in valid_types if product_lower in pt or pt in product_lower]

    if close_matches:
        return f"'{product_type}' not exact match. Did you mean: {', '.join(close_matches)}?"

    return f"'{product_type}' not in standard product types. Use if mentioned explicitly."


@extraction_agent.output_validator
async def validate_extraction(ctx: RunContext[ExtractionDeps], output: LeadExtraction) -> LeadExtraction:
    """Validate extraction output quality

    Args:
        ctx: Run context with dependencies
        output: Extracted lead data

    Returns:
        Validated LeadExtraction

    Raises:
        ModelRetry: If validation fails
    """
    # Check lead quality score
    if output.lead_quality_score < 1 or output.lead_quality_score > 10:
        raise ModelRetry("Lead quality score must be between 1 and 10")

    # Must have at least some extracted data
    if not output.product_type and not output.specific_ingredients:
        raise ModelRetry("Must extract at least product types or specific ingredients")

    # Confidence check
    if output.extraction_confidence < 0 or output.extraction_confidence > 1:
        raise ModelRetry("Extraction confidence must be between 0 and 1")

    # Priority validation
    valid_priorities = ['critical', 'high', 'medium', 'low']
    if output.response_priority not in valid_priorities:
        raise ModelRetry(f"Response priority must be one of: {', '.join(valid_priorities)}")

    logger.info(
        f"✓ Validated extraction: score={output.lead_quality_score}, "
        f"priority={output.response_priority}, confidence={output.extraction_confidence:.2f}"
    )

    return output


class ExtractionAgentWrapper:
    """Wrapper for extraction agent to maintain compatibility with existing code"""

    def __init__(self):
        """Initialize extraction agent"""
        logger.info("Initialized PydanticAI Extraction Agent with OpenRouter")

    def build_extraction_prompt(self, email_data: Dict) -> str:
        """Build extraction prompt (for compatibility)

        Args:
            email_data: Email data

        Returns:
            Formatted prompt
        """
        return f"""Analyze this lead email and extract structured data.

EMAIL DATA:
From: {email_data.get('sender_name', 'Unknown')} <{email_data.get('sender_email')}>
Subject: {email_data.get('subject', 'No subject')}

Body:
{email_data.get('body', '')}

---

Extract:
1. Product types and specific ingredients
2. Delivery formats and certifications requested
3. Business intelligence (quantity, timeline, budget, experience)
4. Distribution channels and geographic region
5. Lead quality score (1-10) and response priority
6. Confidence in extraction accuracy (0-1)

Use the search_knowledge_base tool to validate product types and certifications.
Use the validate_product_type tool to check if product types are supported.
"""

    async def extract_from_email(self, email_data: Dict) -> Optional[Dict]:
        """Extract structured data from email

        Args:
            email_data: Email data dictionary

        Returns:
            Extracted data dictionary or None if failed
        """
        try:
            # Build extraction prompt
            prompt = self.build_extraction_prompt(email_data)

            # Create dependencies
            deps = ExtractionDeps(
                config=settings,
                email_data=email_data
            )

            # Run agent
            result = await extraction_agent.run(prompt, deps=deps)

            # Convert to dictionary for compatibility
            extracted_data = result.output.model_dump()

            logger.info(
                f"Extracted data from {email_data.get('sender_email')}: "
                f"score={extracted_data['lead_quality_score']}, "
                f"priority={extracted_data['response_priority']}"
            )

            return extracted_data

        except Exception as e:
            logger.error(f"Error extracting data: {e}", exc_info=True)
            # Fall back to simple extraction
            return self._fallback_extraction(email_data)

    def _fallback_extraction(self, email_data: Dict) -> Dict:
        """Fallback extraction using keyword matching

        Args:
            email_data: Email data

        Returns:
            Basic extracted data
        """
        logger.warning("Using fallback extraction")

        body = email_data.get('body', '').lower()
        subject = email_data.get('subject', '').lower()
        combined = f"{subject} {body}"

        # Simple keyword matching
        product_types = []
        for product in settings.PRODUCT_TYPES:
            if product.replace('-', ' ') in combined:
                product_types.append(product)

        certifications = []
        for cert in settings.CERTIFICATIONS:
            if cert.replace('-', ' ') in combined:
                certifications.append(cert)

        delivery_formats = []
        for fmt in settings.DELIVERY_FORMATS:
            if fmt in combined:
                delivery_formats.append(fmt)

        score = 5
        if product_types:
            score += 2
        if certifications:
            score += 1

        priority = "medium"
        if score >= 8:
            priority = "high"
        elif score <= 4:
            priority = "low"

        return {
            "product_type": product_types[:3] if product_types else [],
            "specific_ingredients": None,
            "delivery_format": delivery_formats[:2] if delivery_formats else None,
            "certifications_requested": certifications[:3] if certifications else None,
            "estimated_quantity": None,
            "timeline_urgency": "exploring",
            "budget_indicator": None,
            "experience_level": None,
            "distribution_channel": None,
            "has_existing_brand": None,
            "specific_questions": None,
            "geographic_region": None,
            "lead_quality_score": min(score, 10),
            "response_priority": priority,
            "extraction_confidence": 0.3
        }

    async def extract_and_score_batch(self, emails: list[Dict]) -> list[Dict]:
        """Extract data from multiple emails

        Args:
            emails: List of email data dictionaries

        Returns:
            List of extraction results
        """
        results = []

        for email in emails:
            try:
                extracted = await self.extract_from_email(email)

                if extracted:
                    # Add email metadata
                    extracted['sender_email'] = email.get('sender_email')
                    extracted['sender_name'] = email.get('sender_name')
                    extracted['subject'] = email.get('subject')
                    extracted['body'] = email.get('body')
                    extracted['message_id'] = email.get('message_id')
                    extracted['received_at'] = email.get('received_at')

                    results.append(extracted)

            except Exception as e:
                logger.error(f"Error processing email {email.get('message_id')}: {e}")

        logger.info(f"Extracted data from {len(results)}/{len(emails)} emails")
        return results


# Singleton instance
_agent = None

def get_extraction_agent() -> ExtractionAgentWrapper:
    """Get singleton extraction agent instance"""
    global _agent
    if _agent is None:
        _agent = ExtractionAgentWrapper()
    return _agent
```

**Testing**:
Create `tests/test_extraction_agent.py`:
```python
import pytest
from agents.extraction_agent import get_extraction_agent

@pytest.mark.asyncio
async def test_extraction_with_sample_email():
    """Test extraction with sample supplement inquiry"""

    agent = get_extraction_agent()

    sample_email = {
        'sender_email': 'john@acmesupplements.com',
        'sender_name': 'John Doe',
        'subject': 'Probiotic Supplement Manufacturing Inquiry',
        'body': """
        Hi,

        We're looking to develop a line of organic probiotic supplements.
        We need 5000 units for our first order. Do you offer vegan capsules?
        We're targeting a Q2 launch, so somewhat urgent.

        Looking forward to hearing from you.

        Best,
        John
        """,
        'message_id': 'test-001',
        'received_at': '2025-01-15T10:00:00Z'
    }

    result = await agent.extract_from_email(sample_email)

    assert result is not None
    assert "probiotics" in result['product_type'] or "probiotic" in result['product_type']
    assert "organic" in result.get('certifications_requested', [])
    assert "capsule" in result.get('delivery_format', [])
    assert result['lead_quality_score'] >= 6
    assert result['response_priority'] in ['high', 'medium']
    assert "5000" in result.get('estimated_quantity', '')
```

---

### Task 3.2: Update Extraction Agent Imports
**File**: `backend/agents/__init__.py`

**Actions**:
- Verify imports still work
- Update if needed

```python
"""
AI Agents for the Supplement Lead Intelligence System
"""

from agents.extraction_agent import get_extraction_agent, ExtractionAgentWrapper
from agents.response_agent import get_response_agent, ResponseAgentWrapper
from agents.analytics_agent import get_analytics_agent, AnalyticsAgent

__all__ = [
    'get_extraction_agent',
    'ExtractionAgentWrapper',
    'get_response_agent',
    'ResponseAgentWrapper',
    'get_analytics_agent',
    'AnalyticsAgent',
]
```

---

## Phase 4: Refactor Response Agent

### Task 4.1: Refactor Response Agent to PydanticAI
**File**: `backend/agents/response_agent.py`

**Strategy**:
1. Replace `ClaudeAgent()` with PydanticAI `Agent`
2. Add RAG retrieval as agent tool
3. Use `ResponseDraft` as `output_type`
4. Add dynamic system prompt based on lead data
5. Add output validators for draft quality

**Key Implementation**:
```python
"""
Response Agent - Generates draft email responses using RAG
Uses PydanticAI with OpenRouter for contextual response generation
"""
import logging
from typing import Dict, Optional
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIChatModel

from models.agent_responses import ResponseDraft
from models.agent_dependencies import ResponseDeps
from services.pydantic_ai_client import get_response_model
from rag import get_semantic_search
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Initialize PydanticAI agent
response_agent = Agent[ResponseDeps, ResponseDraft](
    model=get_response_model(),
    output_type=ResponseDraft,
    deps_type=ResponseDeps,
    system_prompt="""You are a professional B2B sales representative for Nutricraft Labs,
a premium supplement contract manufacturing company.

Write personalized email responses to potential customer inquiries using:
- Professional but warm B2B tone
- Specific and concrete information from knowledge base
- Clear next steps and call to action
- Maximum 600 words

Use the retrieve_context tool to get accurate information about capabilities, pricing, MOQs, and certifications.
Base all technical details on the retrieved context - never make up information.""",
    retries=2,
)


@response_agent.tool
async def retrieve_context(ctx: RunContext[ResponseDeps], query: str) -> str:
    """Retrieve relevant context from knowledge base

    Args:
        query: Search query for knowledge base

    Returns:
        Relevant context from knowledge base
    """
    try:
        semantic_search = get_semantic_search()

        # Build comprehensive query
        lead_data = ctx.deps.lead_data
        query_parts = [query]

        # Add product types
        if lead_data.get('product_type'):
            query_parts.extend(lead_data['product_type'])

        # Add certifications
        if lead_data.get('certifications_requested'):
            query_parts.extend(lead_data['certifications_requested'])

        combined_query = " ".join(query_parts)

        # Get context
        context = await semantic_search.get_context_for_query(
            query=combined_query,
            max_tokens=3000
        )

        logger.info(f"Retrieved RAG context for query: {query[:50]}")
        return context

    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return "Error retrieving context from knowledge base."


@response_agent.tool
async def get_product_capabilities(ctx: RunContext[ResponseDeps], product_types: list[str]) -> str:
    """Get Nutricraft capabilities for specific product types

    Args:
        product_types: List of product types

    Returns:
        Capabilities information
    """
    try:
        semantic_search = get_semantic_search()

        capabilities = []
        for product_type in product_types:
            query = f"{product_type} manufacturing capabilities MOQ pricing"
            results = await semantic_search.similarity_search(
                query=query,
                top_k=3,
                document_type='capability'
            )

            for r in results:
                capabilities.append(
                    f"Product: {product_type}\n"
                    f"Source: {r['document_name']}\n"
                    f"{r['text'][:300]}"
                )

        if not capabilities:
            return "No specific capabilities found. Use general manufacturing information."

        return "\n\n---\n\n".join(capabilities)

    except Exception as e:
        logger.error(f"Error getting capabilities: {e}")
        return "Error retrieving product capabilities."


@response_agent.system_prompt
async def get_dynamic_system_prompt(ctx: RunContext[ResponseDeps]) -> str:
    """Generate dynamic system prompt based on lead data

    Args:
        ctx: Run context with lead data

    Returns:
        Customized system prompt
    """
    lead_data = ctx.deps.lead_data
    priority = lead_data.get('response_priority', 'medium')

    base_prompt = """You are a professional B2B sales representative for Nutricraft Labs.

Write a personalized email response to this customer inquiry."""

    if priority == 'critical':
        base_prompt += "\n\n⚠️ HIGH PRIORITY LEAD - Provide detailed, comprehensive response with specific pricing and timeline information."
    elif priority == 'high':
        base_prompt += "\n\n✓ HIGH VALUE LEAD - Provide detailed information and offer to schedule a call."
    elif priority == 'low':
        base_prompt += "\n\nℹ️ EXPLORATORY INQUIRY - Provide general information and ask qualifying questions."

    return base_prompt


@response_agent.output_validator
async def validate_response_draft(ctx: RunContext[ResponseDeps], output: ResponseDraft) -> ResponseDraft:
    """Validate response draft quality

    Args:
        ctx: Run context
        output: Draft response

    Returns:
        Validated ResponseDraft

    Raises:
        ModelRetry: If validation fails
    """
    # Check minimum length
    if len(output.draft_content) < 100:
        raise ModelRetry("Draft is too short. Must be at least 100 characters.")

    # Check maximum length (rough word count)
    word_count = len(output.draft_content.split())
    if word_count > settings.MAX_DRAFT_LENGTH + 100:
        raise ModelRetry(f"Draft is too long ({word_count} words). Maximum is {settings.MAX_DRAFT_LENGTH} words.")

    # Must have subject line
    if not output.subject_line or len(output.subject_line) < 5:
        raise ModelRetry("Subject line is missing or too short.")

    # Check for placeholder text
    placeholders = ['[', ']', 'TODO', 'TBD', 'FILL IN']
    for placeholder in placeholders:
        if placeholder in output.draft_content:
            raise ModelRetry(f"Draft contains placeholder text: {placeholder}")

    # Confidence score validation
    if output.confidence_score < 0 or output.confidence_score > 10:
        raise ModelRetry("Confidence score must be between 0 and 10.")

    logger.info(
        f"✓ Validated draft: {len(output.draft_content)} chars, "
        f"confidence={output.confidence_score:.2f}"
    )

    return output


class ResponseAgentWrapper:
    """Wrapper for response agent to maintain compatibility"""

    def __init__(self):
        """Initialize response agent"""
        self.search = get_semantic_search(top_k=settings.TOP_K_RETRIEVAL)
        logger.info("Initialized PydanticAI Response Agent with OpenRouter")

    async def generate_response(self, lead_data: Dict) -> Optional[Dict]:
        """Generate email draft response for a lead

        Args:
            lead_data: Extracted lead data

        Returns:
            Draft data dictionary
        """
        try:
            # Build prompt
            prompt = f"""Generate an email response to this customer inquiry.

CUSTOMER INFORMATION:
From: {lead_data.get('sender_name', 'Customer')} <{lead_data.get('sender_email')}>
Subject: {lead_data.get('subject')}

ORIGINAL MESSAGE:
{lead_data.get('body', '')[:500]}...

EXTRACTED NEEDS:
- Products: {', '.join(lead_data.get('product_type', []))}
- Certifications: {', '.join(lead_data.get('certifications_requested', []) or [])}
- Formats: {', '.join(lead_data.get('delivery_format', []) or [])}
- Quantity: {lead_data.get('estimated_quantity', 'Not specified')}
- Timeline: {lead_data.get('timeline_urgency', 'Not specified')}

Use the retrieve_context and get_product_capabilities tools to get accurate information.
Structure your response professionally with clear sections.
Sign as "Sarah Mitchell, Customer Success Manager, Nutricraft Labs"."""

            # Create dependencies
            deps = ResponseDeps(
                config=settings,
                lead_data=lead_data,
                email_content=lead_data.get('body', '')
            )

            # Run agent
            result = await response_agent.run(prompt, deps=deps)

            # Convert to dictionary
            draft_data = result.output.model_dump()

            logger.info(
                f"Generated draft for {lead_data.get('sender_email')}: "
                f"confidence={draft_data['confidence_score']:.2f}"
            )

            return draft_data

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return self._fallback_response(lead_data)

    def _fallback_response(self, lead_data: Dict) -> Dict:
        """Generate fallback response

        Args:
            lead_data: Lead data

        Returns:
            Basic draft data
        """
        logger.warning("Using fallback response")

        sender_name = lead_data.get('sender_name', 'there')
        products = lead_data.get('product_type', [])

        product_mention = f"{products[0]} supplements" if products else "supplement products"

        content = f"""Dear {sender_name},

Thank you for reaching out to Nutricraft Labs regarding {product_mention}.

We'd love to learn more about your specific needs and provide you with detailed information about our manufacturing capabilities, certifications, and pricing.

Could you please provide some additional details about your project?

I'm happy to schedule a call to discuss your project in detail.

Best regards,
Sarah Mitchell
Customer Success Manager
Nutricraft Labs
(555) 123-4567 | sarah.mitchell@nutricraftlabs.com"""

        subject = lead_data.get('subject', '')
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}" if subject else "Re: Supplement Manufacturing Inquiry"

        return {
            'subject_line': subject,
            'draft_content': content,
            'response_type': 'fallback',
            'confidence_score': 3.0,
            'flags': ['fallback_response_used'],
            'rag_sources': [],
            'status': 'pending'
        }


# Singleton instance
_agent = None

def get_response_agent() -> ResponseAgentWrapper:
    """Get singleton response agent instance"""
    global _agent
    if _agent is None:
        _agent = ResponseAgentWrapper()
    return _agent
```

---

## Phase 5: Analytics Agent (No LLM Needed)

### Task 5.1: Keep Analytics Agent as Pure Python
**File**: `backend/agents/analytics_agent.py`

**Decision**: Analytics agent does NOT need LLM - it's pure SQL/Python logic

**Actions**:
- **NO CHANGES NEEDED**
- Analytics agent is already optimal (SQL queries + aggregations)
- PydanticAI would be overkill for database queries
- Keep existing implementation

**Note**: If we ever want LLM-based insights (e.g., "explain this trend"), we can add a separate `InsightsAgent` later.

---

## Phase 6: Integration & Testing

### Task 6.1: Update Celery Tasks Integration
**File**: `backend/tasks/email_tasks.py`

**Actions**:
- Verify agent imports still work
- Test with sample email data
- Add error handling for PydanticAI exceptions

**Testing**:
```python
# Test extraction
from agents import get_extraction_agent

agent = get_extraction_agent()
result = await agent.extract_from_email(sample_email)
assert result['lead_quality_score'] >= 1
```

**No code changes needed** - wrapper maintains backward compatibility!

---

### Task 6.2: Create Sample Test Emails
**File**: `tests/sample_emails.py` (NEW FILE)

**Purpose**: Sample emails for testing agents

**Implementation**:
```python
"""
Sample email data for testing agents
"""
from datetime import datetime

SAMPLE_EMAILS = [
    {
        'message_id': 'sample-001',
        'sender_email': 'john@acmehealth.com',
        'sender_name': 'John Smith',
        'subject': 'Organic Probiotic Supplement Manufacturing',
        'body': """
Hi,

We're a startup health company looking to launch our first product line -
organic probiotic supplements in vegan capsule format.

We're targeting 10,000 units for the initial production run, with plans to
scale to 50,000 units within 6 months.

Key requirements:
- Organic certification (USDA Organic)
- Non-GMO
- Vegan capsules
- GMP facility
- Third-party testing

Our target launch is Q2 2025, so we're on a medium timeline.

Could you provide:
1. MOQ and pricing for 10k and 50k units
2. Timeline from formulation to delivery
3. Your organic certification details
4. White label services availability

Looking forward to your response.

Best regards,
John Smith
CEO, Acme Health
john@acmehealth.com
        """,
        'received_at': datetime.utcnow()
    },
    {
        'message_id': 'sample-002',
        'sender_email': 'sarah@fitnessbrand.com',
        'sender_name': 'Sarah Johnson',
        'subject': 'Pre-Workout Powder Manufacturing Inquiry',
        'body': """
Hello,

I'm reaching out on behalf of FitnessBrand, an established supplement company
looking for a new manufacturing partner for our pre-workout line.

Product specs:
- Pre-workout powder (30 serving containers)
- Current SKU: 5 flavors
- Monthly volume: 25,000-30,000 units
- Must have NSF Sport certification
- Need custom flavoring capabilities

We're evaluating partners and would like to schedule a call next week if possible.

What's your MOQ for powder manufacturing?

Thanks,
Sarah Johnson
Operations Director
        """,
        'received_at': datetime.utcnow()
    },
    {
        'message_id': 'sample-003',
        'sender_email': 'info@genericcompany.com',
        'sender_name': '',
        'subject': 'Question',
        'body': """
Do you make supplements?
        """,
        'received_at': datetime.utcnow()
    }
]


def get_sample_email(index: int = 0):
    """Get sample email by index

    Args:
        index: Email index (0-2)

    Returns:
        Sample email dictionary
    """
    return SAMPLE_EMAILS[index]


def get_all_sample_emails():
    """Get all sample emails

    Returns:
        List of sample email dictionaries
    """
    return SAMPLE_EMAILS
```

---

### Task 6.3: Create Agent Testing Script
**File**: `tests/test_agents_manual.py` (NEW FILE)

**Purpose**: Manual testing script for agents

**Implementation**:
```python
"""
Manual testing script for PydanticAI agents
Run with: python -m tests.test_agents_manual
"""
import asyncio
import json
from agents import get_extraction_agent, get_response_agent
from tests.sample_emails import get_sample_email


async def test_extraction_agent():
    """Test extraction agent with sample email"""
    print("\n" + "="*80)
    print("Testing Extraction Agent")
    print("="*80)

    agent = get_extraction_agent()
    email = get_sample_email(0)  # High-quality lead

    print(f"\nInput Email:")
    print(f"From: {email['sender_name']} <{email['sender_email']}>")
    print(f"Subject: {email['subject']}")
    print(f"Body: {email['body'][:200]}...")

    print("\n🔄 Running extraction agent...")

    result = await agent.extract_from_email(email)

    print("\n✅ Extraction Results:")
    print(json.dumps(result, indent=2))

    return result


async def test_response_agent(lead_data):
    """Test response agent with extracted lead data"""
    print("\n" + "="*80)
    print("Testing Response Agent")
    print("="*80)

    agent = get_response_agent()

    print("\n🔄 Running response agent...")

    draft = await agent.generate_response(lead_data)

    print("\n✅ Draft Response:")
    print(f"Subject: {draft['subject_line']}")
    print(f"Confidence: {draft['confidence_score']}/10")
    print(f"Type: {draft['response_type']}")
    print(f"Flags: {draft['flags']}")
    print(f"\nContent:\n{draft['draft_content']}")

    return draft


async def main():
    """Run all tests"""
    print("\n🚀 Starting Agent Tests\n")

    # Test extraction
    lead_data = await test_extraction_agent()

    # Test response
    if lead_data:
        draft = await test_response_agent(lead_data)

    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
```

**Run with**:
```bash
docker compose exec backend python -m tests.test_agents_manual
```

---

### Task 6.4: Create Unit Tests
**File**: `tests/test_extraction_agent.py`

**Purpose**: Pytest unit tests for extraction agent

**Implementation**:
```python
"""
Unit tests for extraction agent
"""
import pytest
from agents.extraction_agent import get_extraction_agent
from tests.sample_emails import get_sample_email


@pytest.mark.asyncio
async def test_extraction_high_quality_lead():
    """Test extraction with high-quality lead"""
    agent = get_extraction_agent()
    email = get_sample_email(0)

    result = await agent.extract_from_email(email)

    assert result is not None
    assert 'probiotics' in [p.lower() for p in result['product_type']]
    assert 'organic' in result.get('certifications_requested', [])
    assert 'capsule' in result.get('delivery_format', [])
    assert result['lead_quality_score'] >= 7
    assert result['response_priority'] in ['high', 'critical']
    assert '10000' in result.get('estimated_quantity', '') or '10,000' in result.get('estimated_quantity', '')


@pytest.mark.asyncio
async def test_extraction_medium_quality_lead():
    """Test extraction with medium-quality lead"""
    agent = get_extraction_agent()
    email = get_sample_email(1)

    result = await agent.extract_from_email(email)

    assert result is not None
    assert result['lead_quality_score'] >= 5
    assert 'powder' in result.get('delivery_format', [])


@pytest.mark.asyncio
async def test_extraction_low_quality_lead():
    """Test extraction with low-quality lead"""
    agent = get_extraction_agent()
    email = get_sample_email(2)

    result = await agent.extract_from_email(email)

    assert result is not None
    assert result['lead_quality_score'] <= 4
    assert result['response_priority'] == 'low'
```

**Run with**:
```bash
docker compose exec backend pytest tests/test_extraction_agent.py -v
```

---

## Phase 7: Documentation & Cleanup

### Task 7.1: Update README
**File**: `README.md`

**Actions**:
- Add PydanticAI section
- Update architecture diagram
- Add OpenRouter setup instructions

**Add Section**:
```markdown
## AI Agent Architecture

This system uses **PydanticAI** with **OpenRouter** for AI-powered email processing.

### Agents:

1. **Extraction Agent** (`backend/agents/extraction_agent.py`)
   - Extracts structured lead data from emails
   - Uses PydanticAI with `LeadExtraction` Pydantic model
   - Tools: RAG search, product validation
   - Model: Claude 3.5 Sonnet via OpenRouter

2. **Response Agent** (`backend/agents/response_agent.py`)
   - Generates personalized email responses
   - Uses RAG for accurate technical details
   - Tools: Knowledge base retrieval, capability lookup
   - Model: Claude 3.5 Sonnet via OpenRouter

3. **Analytics Agent** (`backend/agents/analytics_agent.py`)
   - Pure Python/SQL - no LLM needed
   - Tracks trends, generates insights

### Setup OpenRouter:

1. Sign up at https://openrouter.ai/
2. Get API key from dashboard
3. Add to `.env`:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```
4. Rebuild containers:
   ```bash
   docker compose up -d --build
   ```

### Testing Agents:

```bash
# Manual test
docker compose exec backend python -m tests.test_agents_manual

# Unit tests
docker compose exec backend pytest tests/test_extraction_agent.py -v
```
```

---

### Task 7.2: Create Migration Guide
**File**: `planning/pydanticai_migration_guide.md` (NEW FILE)

**Purpose**: Guide for understanding the migration

**Content**:
```markdown
# PydanticAI Migration Guide

## What Changed

### Before (Claude Agent SDK - Non-functional):
```python
from claude_code_agent import ClaudeAgent

agent = ClaudeAgent()
response = await agent.generate_text(prompt, model="claude-3-5-sonnet")
extracted_data = json.loads(response['content'])
```

### After (PydanticAI + OpenRouter):
```python
from pydantic_ai import Agent
from models.agent_responses import LeadExtraction

agent = Agent(model, output_type=LeadExtraction)
result = await agent.run(prompt, deps=deps)
extracted_data = result.output.model_dump()
```

## Key Benefits

1. **Type Safety**: Pydantic models enforce structure
2. **Validation**: Automatic validation + custom validators
3. **Tools**: Agents can call RAG search as tools
4. **Retries**: Automatic retries on validation failure
5. **OpenRouter**: Works with any LLM provider

## Files Modified

- `backend/requirements.txt` - Added pydantic-ai
- `backend/config.py` - Added OpenRouter settings
- `backend/services/pydantic_ai_client.py` - NEW: Model configuration
- `backend/models/agent_responses.py` - NEW: Response models
- `backend/models/agent_dependencies.py` - NEW: Dependency models
- `backend/agents/extraction_agent.py` - Refactored to PydanticAI
- `backend/agents/response_agent.py` - Refactored to PydanticAI
- `tests/` - Added test files

## Backward Compatibility

The `ExtractionAgentWrapper` and `ResponseAgentWrapper` maintain the same public API:

```python
# Old code still works!
agent = get_extraction_agent()
result = await agent.extract_from_email(email_data)
# result is still a dict
```

## Testing

See `tests/test_agents_manual.py` for examples.
```

---

### Task 7.3: Update Environment Templates
**File**: `.env.example`

**Actions**:
- Remove deprecated Claude Agent SDK references
- Add OpenRouter configuration
- Add helpful comments

**Final `.env.example`**:
```env
# Database Configuration
DB_USER=emailagent_user
DB_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
DB_HOST=postgres
DB_PORT=5432
DB_NAME=supplement_leads_db
DATABASE_URL=postgresql://emailagent_user:CHANGE_THIS_SECURE_PASSWORD@postgres:5432/supplement_leads_db

# Email Configuration (Custom IMAP Server)
EMAIL_IMAP_HOST=imap.yourdomain.com
EMAIL_IMAP_PORT=993
EMAIL_SMTP_HOST=smtp.yourdomain.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=contact@nutricraftlabs.com
EMAIL_PASSWORD=YOUR_EMAIL_APP_PASSWORD

# Application
SECRET_KEY=your-secret-key-for-jwt-tokens-CHANGE-THIS
ENVIRONMENT=development
DEBUG=true

# Redis
REDIS_URL=redis://redis:6379/0

# AI Configuration - OpenRouter
# Sign up at: https://openrouter.ai/
OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY_HERE
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_EXTRACTION_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_RESPONSE_MODEL=anthropic/claude-3.5-sonnet

# Model Settings
LLM_TEMPERATURE_EXTRACTION=0.3
LLM_TEMPERATURE_RESPONSE=0.7
LLM_MAX_TOKENS=4000
LLM_TIMEOUT=60

# Optional: OpenAI API key for embeddings (if not using Claude for embeddings)
OPENAI_API_KEY=

# Optional: Monitoring & Error Tracking
SENTRY_DSN=
```

---

## Phase 8: Deployment & Verification

### Task 8.1: Rebuild All Containers
**Commands**:
```bash
# Stop all containers
docker compose down

# Rebuild with no cache
docker compose build --no-cache

# Start all services
docker compose up -d

# Check logs
docker compose logs -f backend
docker compose logs -f celery-worker
```

---

### Task 8.2: Verify Installation
**Script**: `scripts/verify_pydantic_ai.py` (NEW FILE)

```python
"""
Verification script for PydanticAI installation
"""
import sys


def verify_imports():
    """Verify all imports work"""
    print("Checking imports...")

    try:
        import pydantic_ai
        print(f"✅ pydantic-ai version: {pydantic_ai.__version__}")
    except ImportError as e:
        print(f"❌ Failed to import pydantic-ai: {e}")
        return False

    try:
        from pydantic_ai import Agent, RunContext
        print("✅ pydantic_ai.Agent imported")
    except ImportError as e:
        print(f"❌ Failed to import Agent: {e}")
        return False

    try:
        from pydantic_ai.models.openai import OpenAIChatModel
        print("✅ OpenAIChatModel imported")
    except ImportError as e:
        print(f"❌ Failed to import OpenAIChatModel: {e}")
        return False

    try:
        from models.agent_responses import LeadExtraction, ResponseDraft
        print("✅ Agent response models imported")
    except ImportError as e:
        print(f"❌ Failed to import response models: {e}")
        return False

    try:
        from services.pydantic_ai_client import get_extraction_model
        print("✅ PydanticAI client service imported")
    except ImportError as e:
        print(f"❌ Failed to import client service: {e}")
        return False

    return True


def verify_config():
    """Verify configuration"""
    print("\nChecking configuration...")

    try:
        from config import get_settings
        settings = get_settings()

        if not settings.OPENROUTER_API_KEY:
            print("⚠️  OPENROUTER_API_KEY not set in .env")
            return False
        else:
            print(f"✅ OPENROUTER_API_KEY configured (length: {len(settings.OPENROUTER_API_KEY)})")

        print(f"✅ Model: {settings.OPENROUTER_MODEL}")
        print(f"✅ Temperature (extraction): {settings.LLM_TEMPERATURE_EXTRACTION}")
        print(f"✅ Temperature (response): {settings.LLM_TEMPERATURE_RESPONSE}")

        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def main():
    """Run all verifications"""
    print("="*80)
    print("PydanticAI Installation Verification")
    print("="*80 + "\n")

    imports_ok = verify_imports()
    config_ok = verify_config()

    print("\n" + "="*80)
    if imports_ok and config_ok:
        print("✅ All verifications passed!")
        print("="*80)
        return 0
    else:
        print("❌ Some verifications failed")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

**Run**:
```bash
docker compose exec backend python scripts/verify_pydantic_ai.py
```

---

### Task 8.3: Test End-to-End Email Processing
**Test Plan**:

1. **Insert sample email** into database:
```python
# Run in backend container
docker compose exec backend python

from tests.sample_emails import get_sample_email
from tasks.email_tasks import process_email
import asyncio

email = get_sample_email(0)
result = asyncio.run(process_email(email))
print(result)
```

2. **Check database**:
```sql
-- Check leads table
SELECT id, sender_email, lead_quality_score, response_priority
FROM leads
ORDER BY created_at DESC
LIMIT 5;

-- Check drafts table
SELECT id, lead_id, subject_line, confidence_score, status
FROM drafts
ORDER BY created_at DESC
LIMIT 5;
```

3. **Verify Celery processing**:
```bash
docker compose logs -f celery-worker | grep "Extracted data"
```

---

## Summary Checklist

### Phase 1: Foundation ✅
- [ ] Install pydantic-ai package
- [ ] Configure OpenRouter settings
- [ ] Create PydanticAI client service

### Phase 2: Models ✅
- [ ] Create agent response models
- [ ] Create agent dependency models

### Phase 3: Extraction Agent ✅
- [ ] Refactor extraction agent to PydanticAI
- [ ] Add RAG tools
- [ ] Add output validators
- [ ] Update imports

### Phase 4: Response Agent ✅
- [ ] Refactor response agent to PydanticAI
- [ ] Add RAG retrieval tools
- [ ] Add dynamic system prompts
- [ ] Add output validators

### Phase 5: Analytics Agent ✅
- [ ] Keep as pure Python (no changes)

### Phase 6: Testing ✅
- [ ] Create sample test emails
- [ ] Create manual testing script
- [ ] Create unit tests
- [ ] Verify Celery integration

### Phase 7: Documentation ✅
- [ ] Update README
- [ ] Create migration guide
- [ ] Update .env templates

### Phase 8: Deployment ✅
- [ ] Rebuild containers
- [ ] Run verification script
- [ ] Test end-to-end processing
- [ ] Monitor logs

---

## Estimated Time

| Phase | Task | Time |
|-------|------|------|
| 1 | Foundation & Configuration | 45 min |
| 2 | Define Pydantic Models | 1 hour |
| 3 | Refactor Extraction Agent | 2.5 hours |
| 4 | Refactor Response Agent | 2.5 hours |
| 5 | Analytics Agent (no changes) | 0 hours |
| 6 | Testing & Integration | 1.5 hours |
| 7 | Documentation | 45 min |
| 8 | Deployment & Verification | 45 min |
| **Total** | | **~10 hours** |

**Note**: Faster than MCP approach due to:
- No MCP server configuration
- No external service setup
- Simpler tool definitions (just Python functions)

---

## Risk Mitigation

### Risk 1: OpenRouter API Compatibility
**Mitigation**: PydanticAI supports OpenAI-compatible APIs out of the box. OpenRouter is fully compatible.

### Risk 2: RAG Integration
**Mitigation**: RAG tools are simple async functions. Existing `get_semantic_search()` works perfectly.

### Risk 3: Output Validation Failures
**Mitigation**: PydanticAI automatically retries with validator feedback. Set `retries=2`.

### Risk 4: Breaking Changes
**Mitigation**: Wrapper classes maintain backward compatibility. Existing code continues to work.

---

## Success Criteria

1. ✅ All agents use PydanticAI with OpenRouter
2. ✅ Structured outputs validated with Pydantic models
3. ✅ RAG tools integrated into agents
4. ✅ All tests passing
5. ✅ End-to-end email processing working
6. ✅ Documentation updated
7. ✅ Zero breaking changes to existing API

---

## Next Steps After Migration

1. **Tune prompts** for better extraction accuracy
2. **Add more RAG tools** for specific queries (if needed)
3. **Implement streaming** for real-time draft preview
4. **Add LLM-based insights** to analytics agent (optional)
5. **Monitor and optimize** model performance
6. **Consider MCP later** - Only if you need external integrations:
   - Market research (Brave Search MCP)
   - External APIs (custom MCP servers)
   - Real-time web data

---

## Resources

- **PydanticAI Docs**: https://ai.pydantic.dev/
  - Tools: https://ai.pydantic.dev/tools/
  - Agents: https://ai.pydantic.dev/agents/
- **OpenRouter Docs**: https://openrouter.ai/docs
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Project PRD**: `/planning/PRD.md`

---

## Final Notes

### ✅ What This Implementation Includes:
- PydanticAI agents with structured Pydantic outputs
- OpenRouter integration for LLM access
- Custom Python tools for RAG and validation
- Type-safe dependency injection
- Comprehensive testing strategy
- Full backward compatibility

### ❌ What We're NOT Including (Intentionally):
- MCP server integration (not needed for internal tools)
- External service dependencies (keep it simple)
- Over-engineered tooling (YAGNI principle)

### 🎯 Philosophy:
**Start simple. Add complexity only when needed.**

Your current needs are 100% internal:
- Internal knowledge base (RAG)
- Internal database (PostgreSQL)
- Internal configuration (product types, certifications)

Custom PydanticAI tools handle this perfectly. Consider MCP only if requirements change.

---

**Generated**: 2025-10-21 (Updated: Simplified - No MCP)
**Author**: Claude Code
**Status**: Ready for Implementation
**Estimated Time**: ~10 hours (down from 12 hours with MCP approach)
