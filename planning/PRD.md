# Product Requirements Document: Supplement Lead Intelligence System

**Version:** 2.0
**Date:** October 20, 2025
**Status:** Planning Phase
**Company:** NutriCraft Labs

---

## Executive Summary

This document outlines the requirements for building a production-ready AI-powered lead intelligence system for supplement manufacturing. The system monitors contact form emails from potential customers interested in creating custom supplement products, extracts valuable business intelligence, generates analytics on product interests and market trends, and creates contextual draft responses with human approval workflow. Built using Python, Claude Agent SDK, PostgreSQL with vector search capabilities, and a modern web-based dashboard, the system leverages RAG (Retrieval-Augmented Generation) to provide accurate, knowledge-based responses.

---

## 1. Project Overview

### 1.1 Purpose
Build an intelligent lead intelligence system specifically for supplement manufacturing that:
- Monitors contact form emails from potential customers
- Extracts supplement-specific product interests (probiotics, electrolytes, protein, etc.)
- Provides actionable business intelligence and market trend analytics
- Generates contextually appropriate draft responses using RAG-enhanced knowledge base
- Requires human approval before sending responses (with path to progressive automation)
- Tracks product type trends, lead quality, certifications, and customer requirements

### 1.2 Key Differentiators
- **Supplement Industry Focus**: Purpose-built for supplement manufacturing lead qualification
- **RAG-Enhanced Intelligence**: Uses product catalogs, pricing guides, and internal documentation for accurate responses
- **Production-Ready Architecture**: PostgreSQL with pgvector for scalable vector search
- **Web-Based Dashboard**: Modern React interface for approval workflow and analytics visualization
- **Multi-Agent Architecture**: Specialized agents for extraction, analytics, and response generation
- **Progressive Automation**: Tracks performance metrics to enable future auto-approval of high-confidence responses
- **Self-Hosted**: Complete control over sensitive business data and customer information

---

## 2. System Architecture

### 2.1 Multi-Agent System Design

#### **Extraction Agent**
- **Purpose**: Extract structured business intelligence from contact form emails
- **Responsibilities**:
  - Extract supplement product types (probiotics, electrolytes, protein, greens, etc.)
  - Identify specific ingredients requested
  - Detect delivery format preferences (powder, capsule, gummy, liquid)
  - Extract certification requirements (Organic, Non-GMO, GMP, NSF, vegan, etc.)
  - Assess lead quality and experience level
  - Determine timeline urgency and budget indicators
  - Identify distribution channels and business model
  - Extract contact information and company details
  - Detect specific questions and requirements
  - Uses RAG to enhance understanding of technical terms and industry jargon

#### **Analytics Agent**
- **Purpose**: Generate business intelligence and market insights
- **Responsibilities**:
  - Track product type trends over time
  - Identify trending ingredients and formulations
  - Analyze lead quality distributions
  - Calculate certification request patterns
  - Generate daily/weekly/monthly analytics snapshots
  - Identify seasonal trends and market shifts
  - Provide predictive insights on emerging product interests
  - Calculate conversion metrics and response effectiveness

#### **Response Agent**
- **Purpose**: Generate contextually appropriate, knowledge-based email responses
- **Responsibilities**:
  - Draft professional responses using RAG-retrieved context
  - Reference accurate product capabilities from knowledge base
  - Include relevant pricing and MOQ information
  - Maintain consistent professional tone for B2B supplement manufacturing
  - Incorporate company certifications and compliance information
  - Provide specific answers to technical formulation questions
  - Flag complex requests requiring custom formulation expertise
  - Track confidence scores and source attribution
  - Learn from approval feedback for continuous improvement

### 2.2 Technical Stack

**Backend Components:**
- **Language**: Python 3.11+
- **Web Framework**: FastAPI (async, production-ready API)
- **AI Framework**: Claude Agent SDK
- **Email Integration**: Email MCP Server (IMAP/SMTP)
- **Database**: PostgreSQL 15+ with pgvector extension
- **ORM**: SQLAlchemy 2.0
- **Vector Search**: pgvector for RAG embeddings
- **Background Jobs**: Celery with Redis
- **LLM**: Claude Sonnet 4.5 via Anthropic API

**Frontend Components:**
- **Framework**: React 18+
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **Data Visualization**: Recharts or Chart.js
- **State Management**: React Query
- **Routing**: React Router

**RAG System:**
- **Document Processing**: PyPDF2, python-docx, markdown parser
- **Embeddings**: Claude Embeddings or OpenAI ada-002
- **Vector Database**: PostgreSQL pgvector
- **Chunking Strategy**: 512 tokens with 50 token overlap

**Infrastructure:**
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: Alembic
- **Configuration**: YAML for settings, .env for secrets
- **Logging**: Python logging module with structured logs
- **Reverse Proxy**: Nginx (production)

**Development Tools:**
- **Testing**: pytest
- **Code Quality**: Black, Ruff
- **Type Checking**: mypy (optional)
- **API Documentation**: Auto-generated via FastAPI (Swagger/OpenAPI)

---

## 3. Functional Requirements

### 3.1 Email Monitoring & Processing

#### FR-1: Email Inbox Monitoring
- System SHALL continuously monitor dedicated email inbox via IMAP
- System SHALL check for new emails every 30 seconds (configurable)
- System SHALL support multiple email providers (Gmail, Outlook, custom IMAP)
- System SHALL handle connection failures gracefully with automatic retry

#### FR-2: Email Reading & Parsing
- System SHALL extract email metadata (sender, subject, timestamp)
- System SHALL parse email body (plain text and HTML)
- System SHALL identify and extract attachments (metadata only)
- System SHALL handle email threads and maintain conversation context

### 3.2 Lead Data Extraction & Intelligence

#### FR-3: Supplement-Specific Data Extraction
- System SHALL extract product type interests including:
  - Probiotics, Electrolytes, Protein, Greens, Multivitamin, Pre-workout, Post-workout
  - Sleep aids, Nootropics, Collagen, Omega-3, Amino acids, Creatine
  - Weight management, Detox, Energy, Immunity, Joint health
- System SHALL identify specific ingredients mentioned in inquiries
- System SHALL detect delivery format preferences (powder, capsule, gummy, liquid, tablet)
- System SHALL extract certification requirements (Organic, Non-GMO, Vegan, Gluten-free, GMP, NSF, Kosher, Halal, third-party tested)
- System SHALL assess lead quality score (1-10) based on:
  - Completeness of information provided
  - Specificity of requirements
  - Business readiness indicators
  - Budget and volume signals
- System SHALL determine experience level:
  - First-time (exploring, basic questions)
  - Established brand (has existing products)
  - Experienced (technical questions, knows MOQs)
- System SHALL assess timeline urgency (urgent, medium 1-3 months, long-term 6+ months, exploring)
- System SHALL infer budget indicators (startup, mid-market, enterprise)

#### FR-4: Data Collection & Storage
- System SHALL store all processed lead data in PostgreSQL database
- System SHALL maintain email metadata and extracted intelligence
- System SHALL track product type mentions with timestamps
- System SHALL record response drafts, approval status, and feedback
- System SHALL preserve email thread relationships
- System SHALL store vector embeddings for RAG system
- System SHALL maintain version control for knowledge base documents

#### FR-5: RAG (Retrieval-Augmented Generation) System
- System SHALL ingest and process knowledge base documents including:
  - Product catalogs (probiotics, electrolytes, protein, greens, etc.)
  - Pricing guides and MOQ requirements
  - Manufacturing capabilities and services documentation
  - Certifications and compliance information
  - FAQ database
- System SHALL chunk documents into 512-token segments with 50-token overlap
- System SHALL generate embeddings using Claude or OpenAI embedding models
- System SHALL store embeddings in PostgreSQL with pgvector extension
- System SHALL perform semantic search to retrieve relevant context (top-K=10-15 chunks)
- System SHALL provide source attribution for retrieved information
- System SHALL support manual document updates and re-indexing
- System SHALL track which knowledge base sections are referenced in responses
- System SHALL measure retrieval quality and relevance scores

### 3.3 Analytics & Insights

#### FR-6: Statistical Analytics
- System SHALL provide the following supplement-specific statistics:
  - **Product Intelligence**: Product type distribution and trends over time
  - **Lead Quality**: Lead quality score distribution and averages
  - **Certifications**: Most requested certifications and compliance requirements
  - **Ingredients**: Trending ingredients and formulation patterns
  - **Delivery Formats**: Powder vs. capsule vs. gummy vs. liquid preferences
  - **Business Metrics**: Experience level distribution, budget indicators, timeline urgency
  - **Distribution Channels**: Retail, e-commerce, subscription, wholesale breakdown
  - **Geographic**: Regional distribution of leads (if location mentioned)
  - **Operational**: Average response time, approval rate, customer reply rate
- System SHALL calculate trends over time (daily, weekly, monthly)
- System SHALL identify seasonal patterns and emerging product interests
- System SHALL generate analytics snapshots for historical reporting

#### FR-7: Web-Based Analytics Dashboard
- System SHALL provide modern web-based dashboard accessible via browser
- System SHALL display real-time statistics with auto-refresh
- System SHALL provide interactive charts and visualizations
- System SHALL allow filtering by date range (custom, last 7 days, 30 days, 90 days, year)
- System SHALL export reports to CSV and PDF formats
- System SHALL show trending product types and ingredients
- System SHALL provide drill-down capability for detailed analysis
- Dashboard pages SHALL include:
  - **Overview**: Key metrics, charts, recent activity
  - **Inbox**: Draft approval interface
  - **Analytics**: Detailed insights and trends
  - **Leads**: Searchable/filterable lead browser
  - **Knowledge**: Document management interface

### 3.4 Response Generation

#### FR-8: RAG-Enhanced Draft Response Creation
- System SHALL generate draft responses using RAG-retrieved context from:
  - Product catalogs (specific capabilities, ingredients, formulations)
  - Pricing guides and MOQ information
  - Manufacturing capabilities and services
  - Certifications and compliance documentation
  - FAQ database and common questions
- System SHALL maintain professional B2B tone appropriate for supplement manufacturing
- System SHALL include accurate, sourced information with attribution
- System SHALL save drafts without sending automatically
- System SHALL calculate confidence scores for each draft
- System SHALL flag drafts requiring special attention:
  - Complex custom formulation requests
  - Pricing negotiations
  - Regulatory/compliance questions
  - Out-of-scope product requests
- System SHALL provide source attribution showing which documents were referenced
- System SHALL handle multiple question types:
  - Initial inquiries (general interest)
  - Pricing and MOQ questions
  - Technical formulation questions
  - Certification and compliance questions
  - Sample requests
  - Timeline and production schedule questions

#### FR-9: Progressive Learning System
- System SHALL track approval vs. rejection rates per draft type
- System SHALL record edits made to drafts (edit distance, common changes)
- System SHALL collect rejection reasons and feedback
- System SHALL monitor customer response sentiment after sending
- System SHALL identify confidence thresholds for future auto-approval
- System SHALL maintain audit log of all approval decisions
- System SHALL support A/B testing of response patterns

### 3.5 Approval Workflow

#### FR-10: Web-Based Approval Interface
- System SHALL queue all draft responses for approval
- System SHALL provide web-based interface for reviewing drafts
- System SHALL display in approval interface:
  - **Original email** (left panel):
    - Sender information and contact details
    - Full email content
    - All extracted data (product types, quality score, certifications, etc.)
    - Lead quality score and priority level
  - **Generated response** (right panel):
    - Subject line (editable)
    - Draft body (editable with inline editor)
    - Confidence score
    - Flags and special attention notes
    - Source attribution (which documents were referenced)
    - RAG context used
- System SHALL allow approval actions:
  - **Approve & Send**: Send draft as-is
  - **Edit & Send**: Modify draft inline before sending
  - **Reject with Feedback**: Decline with reason for learning
  - **Save for Later**: Keep in pending queue
  - **Flag for Discussion**: Mark for team review
- System SHALL provide keyboard shortcuts for efficient workflow
- System SHALL support inline editing with rich text editor
- System SHALL show real-time preview of email before sending

#### FR-11: Draft Management
- System SHALL track draft status (pending, approved, rejected, sent, edited)
- System SHALL log all approval decisions with timestamp and reviewer
- System SHALL record feedback and edit summaries for learning
- System SHALL allow bulk approval for high-confidence, low-risk drafts
- System SHALL provide priority sorting (critical, high, medium, low)
- System SHALL send email confirmation after successful send
- System SHALL handle SMTP errors gracefully with retry logic
- System SHALL maintain draft history and audit trail

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### NFR-1: Processing Speed
- Lead data extraction SHALL complete within 3-7 seconds (including RAG retrieval)
- Draft generation with RAG SHALL complete within 5-15 seconds
- Analytics queries SHALL return within 2 seconds
- Dashboard page loads SHALL complete within 1 second
- System SHALL handle 10-50 emails/day efficiently (low-volume, high-quality processing)
- RAG semantic search SHALL return within 1-2 seconds
- Background job processing SHALL not block web interface

#### NFR-2: Reliability
- System SHALL achieve 99.5% uptime during business hours
- System SHALL implement automatic error recovery
- System SHALL handle API rate limits gracefully
- System SHALL retry failed operations up to 3 times

### 4.2 Security

#### NFR-3: Data Protection
- System SHALL store email credentials securely in .env file
- System SHALL encrypt sensitive data at rest
- System SHALL use secure connections (TLS/SSL) for email access
- System SHALL implement access controls for approval interface

#### NFR-4: Privacy
- System SHALL not store email attachments (metadata only)
- System SHALL support data retention policies
- System SHALL allow purging of old data
- System SHALL comply with email privacy regulations

### 4.3 Maintainability

#### NFR-5: Code Quality
- System SHALL follow PEP 8 Python style guidelines
- System SHALL include comprehensive error handling
- System SHALL provide detailed logging at appropriate levels
- System SHALL include inline documentation and docstrings

#### NFR-6: Monitoring & Observability
- System SHALL log all operations to file
- System SHALL track performance metrics
- System SHALL alert on errors and anomalies
- System SHALL provide health check endpoints

### 4.4 Scalability

#### NFR-7: Growth Support
- System SHALL support multiple email accounts (future enhancement)
- System SHALL handle growing database size (100,000+ leads with vector embeddings)
- PostgreSQL with pgvector SHALL scale to millions of embeddings
- System SHALL support distributed deployment (future enhancement)
- Database schema SHALL be version-controlled using Alembic migrations
- System SHALL support horizontal scaling of web frontend
- System SHALL support read replicas for analytics queries (future)

---

## 5. System Components

### 5.1 Project Structure

```
supplement-lead-system/
├── .env                          # API keys, DB credentials, email config
├── .env.example                  # Environment template
├── docker-compose.yml            # PostgreSQL + Redis + App services
├── requirements.txt              # Python dependencies
├── config.yaml                   # System configuration
├── README.md                     # Project documentation
│
├── backend/
│   ├── main.py                   # FastAPI application entry point
│   ├── database.py               # Database connection & models
│   ├── config.py                 # Configuration management
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── extraction_agent.py   # Lead data extraction agent
│   │   ├── analytics_agent.py    # Analytics generation agent
│   │   └── response_agent.py     # Draft response generation agent
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── ingestion.py          # Document ingestion pipeline
│   │   ├── embeddings.py         # Embedding generation
│   │   ├── retrieval.py          # Semantic search
│   │   └── chunking.py           # Text chunking utilities
│   │
│   ├── services/
│   │   ├── email_monitor.py      # Email polling service
│   │   ├── draft_service.py      # Draft management
│   │   └── analytics_service.py  # Analytics calculations
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── leads.py              # Lead CRUD endpoints
│   │   ├── drafts.py             # Draft approval endpoints
│   │   ├── analytics.py          # Analytics endpoints
│   │   └── knowledge.py          # Knowledge base management
│   │
│   ├── models/
│   │   ├── schemas.py            # Pydantic request/response models
│   │   └── database.py           # SQLAlchemy ORM models
│   │
│   └── tasks/
│       ├── celery_app.py         # Celery configuration
│       └── workers.py            # Background job workers
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── DraftReview.jsx       # Draft approval component
│       │   ├── LeadCard.jsx
│       │   ├── Analytics/
│       │   │   ├── TrendChart.jsx
│       │   │   ├── ProductPieChart.jsx
│       │   │   └── MetricsCards.jsx
│       │   └── Common/
│       ├── pages/
│       │   ├── Dashboard.jsx         # Overview page
│       │   ├── Inbox.jsx             # Draft approval page
│       │   ├── Analytics.jsx         # Analytics & insights
│       │   ├── Leads.jsx             # Lead browser
│       │   └── Knowledge.jsx         # Document management
│       ├── services/
│       │   └── api.js                # API client
│       ├── App.jsx
│       └── main.jsx
│
├── knowledge/                    # Knowledge base documents
│   ├── products/
│   │   ├── probiotics.md
│   │   ├── electrolytes.md
│   │   ├── protein.md
│   │   └── greens.md
│   ├── pricing/
│   │   └── moq-pricing-guide.md
│   ├── capabilities/
│   │   └── manufacturing-services.md
│   ├── certifications/
│   │   └── available-certifications.md
│   └── faq/
│       └── common-questions.md
│
├── scripts/
│   ├── ingest_knowledge.py       # Initial document ingestion
│   ├── update_knowledge.py       # Re-index documents
│   └── migrate_db.py             # Database migration helper
│
├── tests/
│   ├── test_extraction.py
│   ├── test_rag.py
│   ├── test_response.py
│   └── test_api.py
│
├── alembic/                      # Database migrations
│   ├── alembic.ini
│   └── versions/
│
└── logs/
    └── system.log
```

### 5.2 Database Schema (PostgreSQL)

#### Leads Table
```sql
CREATE TABLE leads (
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

    -- Supplement-specific data
    product_type TEXT[],  -- Array of product types
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
    response_priority TEXT,

    -- Additional metadata
    specific_questions TEXT[],
    geographic_region TEXT,
    extraction_confidence FLOAT,
    internal_notes TEXT
);

CREATE INDEX idx_leads_received ON leads(received_at DESC);
CREATE INDEX idx_leads_product_type ON leads USING GIN(product_type);
CREATE INDEX idx_leads_quality ON leads(lead_quality_score DESC);
```

#### Drafts Table
```sql
CREATE TABLE drafts (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Draft content
    subject_line TEXT NOT NULL,
    draft_content TEXT NOT NULL,

    -- Status and metadata
    status TEXT NOT NULL DEFAULT 'pending',
    response_type TEXT,
    confidence_score FLOAT,
    flags TEXT[],
    rag_sources TEXT[],  -- Which documents were referenced

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
    customer_sentiment TEXT,

    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected', 'sent', 'edited'))
);

CREATE INDEX idx_drafts_status ON drafts(status);
CREATE INDEX idx_drafts_pending ON drafts(status) WHERE status = 'pending';
```

#### Document Embeddings Table (RAG)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,

    -- Document identification
    document_name TEXT NOT NULL,
    document_type TEXT NOT NULL,
    section_title TEXT,

    -- Content and embeddings
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding vector(1536),  -- OpenAI ada-002 or Claude embeddings

    -- Metadata
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embeddings_vector ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_embeddings_type ON document_embeddings(document_type);
```

#### Product Type Trends Table
```sql
CREATE TABLE product_type_trends (
    id SERIAL PRIMARY KEY,
    product_type TEXT NOT NULL,
    date DATE NOT NULL,
    mention_count INTEGER DEFAULT 1,
    lead_count INTEGER DEFAULT 1,
    avg_quality_score FLOAT,

    UNIQUE(product_type, date)
);

CREATE INDEX idx_trends_date ON product_type_trends(date DESC);
```

#### Analytics Snapshots Table
```sql
CREATE TABLE analytics_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    period_type TEXT NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(snapshot_date, period_type)
);

CREATE INDEX idx_snapshots_date ON analytics_snapshots(snapshot_date DESC);
```

---

## 6. User Interface Requirements

### 6.1 Web Dashboard Overview

The system SHALL provide a modern, responsive web-based dashboard accessible via browser (desktop and tablet). All interfaces SHALL follow consistent design patterns using TailwindCSS components.

### 6.2 Dashboard Page: Overview

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Navigation Bar                                           │
│ Overview | Inbox (12) | Analytics | Leads | Knowledge  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Metrics Cards Row:                                       │
│ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐ │
│ │ 47 Leads  │ │ 12 Pending│ │ Score 8.2 │ │ 89%     │ │
│ │ This Week │ │ Drafts    │ │ Avg       │ │ Approved│ │
│ └───────────┘ └───────────┘ └───────────┘ └─────────┘ │
│                                                          │
│ Product Type Distribution (Interactive Pie Chart)        │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Probiotics: 35% | Electrolytes: 25% | Protein: 20%  ││
│ │ Greens: 12% | Other: 8%                             ││
│ └──────────────────────────────────────────────────────┘│
│                                                          │
│ Lead Quality Over Time (Line Chart - Last 30 Days)      │
│                                                          │
│ Recent Activity Feed                                     │
│ • New lead: john@startup.com (Probiotic, Score: 8)      │
│ • Draft approved: jane@wellness.co                       │
│ • Draft sent: mike@fitness.com                           │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Dashboard Page: Inbox (Approval Workflow)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│ Inbox - Draft Approvals (12 Pending)                    │
│ [High Priority] [Medium] [Low] | Sort: Newest First ▼   │
├──────────────────────────────┬──────────────────────────┤
│ Pending Queue (Left Sidebar) │ Draft Review (Main Area) │
│                              │                          │
│ ┌──────────────────────────┐ │ ┌──────────────────────┐│
│ │ [HIGH] Custom Probiotic  │ │ │ ORIGINAL EMAIL       ││
│ │ john@startup.com         │ │ │                      ││
│ │ 2 hours ago              │ │ │ From: john@startup   ││
│ │ Confidence: 8.7/10       │ │ │ Company: HealthCo    ││
│ │ [Selected]               │ │ │                      ││
│ └──────────────────────────┘ │ │ Product Type:        ││
│                              │ │ • Probiotics ✓       ││
│ ┌──────────────────────────┐ │ │ Quality Score: 8/10  ││
│ │ [MEDIUM] Electrolyte Inquiry││ │                      ││
│ │ sarah@brands.io          │ │ │ [Full email body...] ││
│ │ 5 hours ago              │ │ └──────────────────────┘│
│ │ Confidence: 7.2/10       │ │                          │
│ └──────────────────────────┘ │ ┌──────────────────────┐│
│                              │ │ GENERATED RESPONSE   ││
│ ... (10 more drafts)         │ │                      ││
│                              │ │ Subject: [Editable]  ││
│                              │ │                      ││
│                              │ │ [Draft body with     ││
│                              │ │  inline editing]     ││
│                              │ │                      ││
│                              │ │ Sources Used:        ││
│                              │ │ ✓ Probiotic Catalog  ││
│                              │ │ ✓ MOQ Pricing Guide  ││
│                              │ │                      ││
│                              │ │ Confidence: 8.7/10   ││
│                              │ │ Flags: None          ││
│                              │ └──────────────────────┘│
│                              │                          │
│                              │ [Approve & Send]         │
│                              │ [Edit & Send]            │
│                              │ [Reject w/ Feedback]     │
│                              │ [Save for Later]         │
└──────────────────────────────┴──────────────────────────┘
```

### 6.4 Dashboard Page: Analytics & Insights

```
┌─────────────────────────────────────────────────────────┐
│ Analytics & Business Intelligence                        │
│ Time Period: [Last 7 Days ▼] [Custom Range] [Export CSV]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Product Type Trends (Line Chart - Interactive)          │
│ Probiotics ━━━  Electrolytes ━━━  Protein ━━━           │
│                                                          │
│ ┌──────────────────────┬──────────────────────────────┐ │
│ │ Certifications       │ Top Ingredients              │ │
│ │ Requested (Heatmap)  │                              │ │
│ │                      │ 1. CFU Strains (47 mentions) │ │
│ │ Organic    ████████  │ 2. Whey Protein (34)         │ │
│ │ Non-GMO    ██████    │ 3. Electrolyte Blend (28)    │ │
│ │ Vegan      ████      │ 4. Greens Mix (21)           │ │
│ │ GMP        ███████   │ 5. Collagen (18)             │ │
│ └──────────────────────┴──────────────────────────────┘ │
│                                                          │
│ Lead Quality Distribution | Timeline Urgency Breakdown   │
│ Budget Indicators | Distribution Channels               │
│                                                          │
│ Question Category Analysis (Bar Chart)                   │
└─────────────────────────────────────────────────────────┘
```

### 6.5 Dashboard Page: Lead Browser

```
┌─────────────────────────────────────────────────────────┐
│ All Leads                                                │
│ [Search...] Filter: [All ▼] [Probiotic ▼] [Score: 8+ ▼]│
├─────────────────────────────────────────────────────────┤
│ Sender    │ Products │ Score │ Urgency │ Date   │Actions│
│───────────┼──────────┼───────┼─────────┼────────┼───────│
│ john@st.. │Probiotic │ 8/10  │ Medium  │2h ago  │[View] │
│ sarah@br..│Electro.. │ 7/10  │ High    │5h ago  │[View] │
│ ...       │          │       │         │        │       │
└─────────────────────────────────────────────────────────┘
```

### 6.6 Dashboard Page: Knowledge Management

```
┌─────────────────────────────────────────────────────────┐
│ Knowledge Base Documents                                 │
│ [Upload New Document] [Re-index All]                     │
├─────────────────────────────────────────────────────────┤
│ Document Name          │ Type     │ Chunks │ Last Update│
│────────────────────────┼──────────┼────────┼────────────│
│ probiotics.md          │ Product  │ 24     │ 2 days ago │
│ moq-pricing-guide.md   │ Pricing  │ 12     │ 1 week ago │
│ available-certs.md     │ Cert.    │ 8      │ 3 days ago │
│ ...                    │          │        │            │
├─────────────────────────────────────────────────────────┤
│ Document Usage Statistics:                               │
│ Most referenced in responses this week                   │
│ 1. Probiotic Product Catalog (34 times)                  │
│ 2. MOQ Pricing Guide (28 times)                          │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Timeline

### Phase 1: Foundation & Infrastructure (Week 1)
**Objectives:**
- Set up PostgreSQL database with pgvector extension
- Configure Docker Compose environment
- Set up FastAPI backend structure
- Configure Email MCP server
- Create React frontend scaffold
- Implement database schema with migrations
- Set up basic email monitoring

**Deliverables:**
- PostgreSQL database with full schema
- Docker Compose configuration (DB + Redis + App)
- FastAPI project structure with basic endpoints
- React frontend scaffold with routing
- Email connection working
- Alembic migrations setup
- Basic email reading and storage in leads table

**Success Criteria:**
- Can connect to email inbox via MCP
- Can read and store emails in PostgreSQL
- Database schema created with proper indexes
- FastAPI serving basic health check endpoints
- React app running locally

---

### Phase 2: RAG System Implementation (Week 2)
**Objectives:**
- Implement document ingestion pipeline
- Set up text extraction for PDF/Markdown/DOCX
- Implement chunking strategy (512 tokens, 50 overlap)
- Generate embeddings using Claude/OpenAI
- Store embeddings in pgvector
- Implement semantic search retrieval
- Test RAG quality with sample documents

**Deliverables:**
- Document ingestion script (ingest_knowledge.py)
- Embedding generation module
- Semantic search implementation
- Initial knowledge base ingested:
  - Product catalogs (probiotics, electrolytes, protein, greens)
  - Pricing guides
  - Certifications documentation
  - FAQ database
- RAG retrieval working with confidence scores

**Success Criteria:**
- Documents successfully ingested and chunked
- Embeddings stored in PostgreSQL
- Semantic search returns relevant results
- Can retrieve top-K relevant chunks for sample queries
- Source attribution working

---

### Phase 3: Agents & Background Processing (Week 3)
**Objectives:**
- Implement Extraction Agent (with RAG)
- Implement Response Agent (with RAG)
- Implement Analytics Agent
- Set up Celery background jobs
- Implement draft creation workflow
- Test end-to-end email → draft flow

**Deliverables:**
- Extraction Agent extracting supplement-specific data
- Response Agent generating RAG-enhanced drafts
- Analytics Agent calculating statistics
- Celery workers processing emails in background
- Draft storage in database
- Email-to-draft complete workflow
- Agent coordination logic

**Success Criteria:**
- Emails automatically processed by extraction agent
- Supplement-specific data extracted (product types, certifications, etc.)
- Drafts generated using RAG-retrieved context
- Background processing works without blocking
- Source attribution included in drafts
- Analytics snapshots generated

---

### Phase 4: Web Approval Interface (Week 4)
**Objectives:**
- Build Inbox/Approval page (React)
- Implement draft review interface
- Add inline editing capability
- Implement approval workflow actions
- Integrate email sending
- Add feedback collection for learning
- Implement priority sorting and filtering

**Deliverables:**
- Inbox page with pending drafts queue
- Draft review interface (original email + generated response)
- Inline rich text editor for drafts
- Approval actions (approve, edit, reject, save)
- SMTP integration for sending
- Feedback collection forms
- Priority and confidence-based filtering

**Success Criteria:**
- Can view all pending drafts
- Can review original email and generated response side-by-side
- Can edit drafts inline before sending
- Can approve and send emails successfully
- Rejection feedback captured for learning
- Bulk approval working for high-confidence drafts

---

### Phase 5: Analytics Dashboard & Production Polish (Week 5)
**Objectives:**
- Build Overview dashboard page
- Build Analytics & Insights page
- Build Lead browser page
- Build Knowledge management page
- Implement data visualizations (charts, graphs)
- Add export functionality (CSV, PDF)
- Performance optimization
- Comprehensive monitoring and logging
- Complete documentation

**Deliverables:**
- All 5 dashboard pages complete and functional
- Interactive charts (Recharts/Chart.js):
  - Product type trends (line chart)
  - Lead quality distribution (bar chart)
  - Certifications heatmap
  - Ingredient trends
- Export to CSV/PDF functionality
- Lead search and filtering
- Document upload and re-indexing UI
- Performance optimizations (caching, query optimization)
- Monitoring and alerting setup
- User documentation and technical docs

**Success Criteria:**
- All dashboard pages render correctly
- Charts display real data accurately
- Export functionality works
- System handles expected load (10-50 emails/day)
- Performance meets NFR requirements
- System runs reliably for 7 consecutive days
- Documentation complete

---

## 8. Risk Assessment & Mitigation

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Email provider API changes | Medium | High | Use standard IMAP/SMTP protocols; maintain flexible configuration |
| Claude API rate limits | Low | Medium | Implement request queuing and caching; monitor usage; low volume reduces risk |
| Database performance degradation | Low | Medium | PostgreSQL with proper indexes and pgvector optimization; connection pooling |
| Email parsing errors | High | Low | Robust error handling; log failures for manual review |
| RAG retrieval quality issues | Medium | Medium | Continuous monitoring of retrieval relevance; manual knowledge base curation |
| Embedding API costs | Low | Medium | Batch embedding generation; cache embeddings; reuse for similar queries |

### 8.2 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Inappropriate response generation | Low | High | Mandatory human approval; safety hooks; content filtering |
| Missed critical emails | Low | Critical | Urgency detection; alerting for high-priority items |
| System downtime | Medium | High | Automatic restart; monitoring; alerting |
| Learning from incorrect approvals | Medium | Medium | Feedback mechanism; periodic review of learned patterns |

---

## 9. Success Metrics

### 9.1 Performance Metrics
- **Lead Processing Time**: ≤7 seconds for extraction (including RAG retrieval)
- **Draft Generation Time**: ≤15 seconds for RAG-enhanced response
- **Dashboard Load Time**: ≤1 second for page loads
- **System Uptime**: ≥99.5% during business hours
- **RAG Retrieval Speed**: ≤2 seconds for semantic search

### 9.2 Quality Metrics
- **Extraction Accuracy**: ≥90% for product type identification (manual review sample)
- **Draft Approval Rate**: ≥70% of drafts approved without edits
- **RAG Relevance**: ≥85% of retrieved chunks rated as relevant by reviewers
- **Source Attribution Accuracy**: 100% of drafts show correct document sources
- **Lead Quality Scoring**: ≥80% agreement with manual scoring

### 9.3 Business Metrics
- **Response Time**: Respond to all leads within 24 hours (vs. 48-72 hours manual)
- **Lead Intelligence**: Track 15+ data points per lead automatically
- **Market Insights**: Identify top 5 trending product types each month
- **Certification Trends**: Track emerging certification requests (quarterly)
- **Conversion Support**: Provide data-driven insights on high-quality leads
- **Knowledge Base ROI**: Measure response accuracy improvement with RAG vs. without

### 9.4 Progressive Automation Metrics (for future auto-approval)
- **Confidence Correlation**: Track confidence score vs. approval rate
- **Edit Distance**: Measure average edits made to drafts
- **Category-Based Performance**: Identify which lead types have highest approval rates
- **Auto-Approval Readiness**: Define threshold when ≥95% approval rate achieved for category

---

## 10. Dependencies & Prerequisites

### 10.1 Technical Dependencies
- **Python**: 3.11 or higher
- **Node.js**: 18+ (for React frontend)
- **PostgreSQL**: 15+ with pgvector extension
- **Redis**: 6+ (for Celery background jobs)
- **Docker & Docker Compose**: For containerized deployment
- **Claude Code Max subscription**: For Anthropic API access
- **Dedicated email account**: With IMAP/SMTP access
- **Stable internet connection**: For API calls and email monitoring
- **Server/Infrastructure**: Minimum 4GB RAM, 20GB storage (for PostgreSQL + vectors)

### 10.2 External Services
- **Anthropic API** (Claude Sonnet 4.5): For agents and embeddings
- **Email provider**: Gmail, Outlook, or custom IMAP/SMTP
- **OpenAI API** (optional): For embeddings if not using Claude
- **Email MCP Server**: For email integration

### 10.3 Knowledge Base Requirements
**Must-Have Documents (ready for ingestion):**
- **Product Catalogs**: Detailed information for each supplement type
  - Probiotics (strains, CFU counts, benefits)
  - Electrolytes (minerals, formulations)
  - Protein (types, sources, blends)
  - Greens, multivitamins, etc.
- **Pricing & MOQ Guides**: Minimum order quantities, pricing tiers, lead times
- **Manufacturing Capabilities**: Services offered, capacity, specializations
- **Certifications Documentation**: Available certifications, requirements, costs, timelines
- **FAQ Database**: Common questions about process, ingredients, compliance

**Optional Documents:**
- Sample formulations
- Case studies
- Regulatory compliance guides
- Ingredient sourcing documentation

---

## 11. Future Enhancements (Post-MVP)

### 11.1 Short-term (3-6 months)
- **Progressive Auto-Approval**: Auto-send high-confidence responses for proven categories
- **Email Template Management**: Customizable templates for different lead types
- **Slack/Email Notifications**: Real-time alerts for high-priority leads
- **Mobile-Responsive Dashboard**: Full mobile support for approval workflow
- **Attachment Handling**: Process PDFs and documents attached to emails
- **CRM Integration**: Sync lead data with HubSpot/Salesforce
- **Advanced Lead Scoring**: ML-based lead quality prediction

### 11.2 Long-term (6-12 months)
- **Multiple Product Lines**: Support for different business units/brands
- **Multi-language Support**: Handle inquiries in Spanish, French, etc.
- **Competitor Intelligence**: Track and analyze competitor mentions
- **Advanced Analytics**: Predictive analytics for seasonal trends
- **Customer Journey Tracking**: Full lifecycle from inquiry to production
- **Automated Follow-ups**: Smart follow-up sequences for non-responders
- **Voice/Video Call Scheduling**: Calendar integration for high-value leads

### 11.3 Advanced Features
- **Fine-tuned Model**: Custom fine-tuned model on approved responses
- **Automatic Knowledge Base Updates**: Ingest new blog posts/updates automatically
- **A/B Testing Framework**: Test different response approaches systematically
- **Customer Segmentation**: Automatic grouping by company size, product interest, etc.
- **Response Effectiveness Scoring**: Track conversion rates by response pattern
- **Real-time Market Intelligence**: Daily reports on emerging supplement trends

---

## 12. Deployment Strategy

### 12.1 Development Environment
- **Docker Compose**: PostgreSQL + Redis + Backend + Frontend locally
- **Hot Reload**: FastAPI auto-reload, Vite HMR for React
- **Development Email Account**: Separate test inbox
- **Git Version Control**: GitHub/GitLab repository
- **Local pgAdmin**: For database inspection
- **Alembic Migrations**: Database schema versioning

### 12.2 Production Deployment Options

#### Option A: Docker Compose (Recommended)
**Advantages:**
- Single command deployment (`docker-compose up -d`)
- Environment isolation
- Easy updates and rollback
- Consistent across environments
- Built-in service orchestration

**Services:**
```yaml
services:
  - postgres (with pgvector)
  - redis
  - backend (FastAPI + Celery worker)
  - frontend (Nginx serving React build)
  - celery-worker (background jobs)
  - celery-beat (scheduled tasks)
```

#### Option B: Traditional VPS Deployment
- **Application Server**: Gunicorn + Uvicorn workers for FastAPI
- **Web Server**: Nginx reverse proxy for frontend + API
- **Process Manager**: Supervisor or systemd for services
- **Database**: Managed PostgreSQL (DigitalOcean, AWS RDS, etc.)
- **Cache**: Managed Redis or self-hosted

#### Option C: Cloud Platform (Future)
- **Kubernetes**: For larger scale or multi-tenant
- **Serverless**: Partial serverless for agents (AWS Lambda, Cloud Run)
- **Managed Services**: AWS RDS for PostgreSQL, ElastiCache for Redis

### 12.3 Monitoring & Maintenance

**Daily:**
- Health check endpoint monitoring
- Email processing queue status
- Error log review (critical errors only)

**Weekly:**
- Analytics review and insights extraction
- Draft approval rate analysis
- RAG retrieval quality spot check
- Database backup verification

**Monthly:**
- Performance optimization review
- Knowledge base updates and re-indexing
- Security patches and dependency updates
- User feedback collection and prioritization

**Quarterly:**
- Full security audit
- Database optimization (VACUUM, index analysis)
- Cost optimization review
- Feature roadmap planning

**Continuous:**
- Automated database backups (daily, retained 30 days)
- Application logs rotation
- Uptime monitoring with alerts
- SSL certificate auto-renewal

---

## 13. Cost Estimates

### 13.1 Development Costs
- **Developer Time**: 5 weeks × 40 hours = 200 hours
- **Claude API Costs** (development): ~$50-100 for testing/development
- **Email Service**: $0 (using existing contact form email)
- **Infrastructure** (development): $0 (local Docker Compose)

**Total Development Cost**: ~200 hours developer time + $50-100 API costs

### 13.2 Operational Costs (Monthly)

**Required Services:**
- **Claude API**: ~$50-200/month (depends on volume)
  - Estimated: 10-50 emails/day × 2 agent calls each = 600-3000 API calls/month
  - RAG embeddings: ~$5-10/month (mostly one-time for initial ingestion)
- **PostgreSQL Hosting**: $15-50/month
  - Self-hosted: $0 (included in VPS)
  - Managed (DigitalOcean, AWS RDS): $15-50/month
- **VPS/Server**: $20-50/month
  - DigitalOcean Droplet (4GB RAM): $24/month
  - AWS Lightsail: $20-40/month
  - Hetzner: $15-30/month (better value)
- **Email Service**: $0 (using existing provider)
- **Domain & SSL**: $15/year (~$1.25/month) - if needed
- **Backup Storage**: $5-10/month (optional managed backups)

**Optional Services:**
- **Redis Cloud**: $0-10/month (or self-hosted for $0)
- **Monitoring** (Sentry, etc.): $0-25/month
- **Error Tracking**: $0 (free tier sufficient)

**Total Estimated Monthly Cost**: $85-315/month
- **Minimal Setup** (self-hosted): ~$85/month (Claude API + VPS)
- **Managed Services**: ~$150-200/month (Claude API + managed DB + VPS)
- **Premium** (higher volume): ~$315/month

### 13.3 Cost Optimization Strategies
- **Embedding Caching**: Generate embeddings once, reuse indefinitely
- **Batch Processing**: Group API calls to reduce overhead
- **Response Caching**: Cache common response patterns
- **Progressive Automation**: Reduce API calls as auto-approval increases
- **Self-Hosted PostgreSQL**: Save $15-50/month vs. managed
- **Volume Monitoring**: Track API usage to optimize prompt lengths

---

## 14. Acceptance Criteria

### 14.1 MVP Release Criteria
- [ ] **Email Monitoring**: System monitors contact form inbox continuously
- [ ] **Data Extraction**: Supplement-specific data extracted with >90% accuracy
  - [ ] Product types identified correctly
  - [ ] Certifications detected accurately
  - [ ] Lead quality scores match manual assessment (≥80% agreement)
- [ ] **RAG System**: Knowledge base ingested and functional
  - [ ] All product catalogs, pricing guides, and certifications indexed
  - [ ] Semantic search returns relevant results
  - [ ] Source attribution working correctly
- [ ] **Draft Generation**: Responses generated with RAG context
  - [ ] Drafts reference accurate knowledge base information
  - [ ] Confidence scores calculated
  - [ ] Sources properly attributed
- [ ] **Web Dashboard**: All 5 pages functional
  - [ ] Overview page displays key metrics
  - [ ] Inbox page allows draft approval
  - [ ] Analytics page shows trends and insights
  - [ ] Lead browser allows search/filter
  - [ ] Knowledge management allows document upload
- [ ] **Approval Workflow**: Complete approval process working
  - [ ] Can approve and send drafts
  - [ ] Can edit drafts inline
  - [ ] Can reject with feedback
  - [ ] Feedback captured for learning
- [ ] **Analytics**: Product type trends tracked over time
- [ ] **Stability**: System runs for 7 consecutive days without critical errors
- [ ] **Documentation**: User guide and technical documentation complete

### 14.2 Production Ready Criteria
- [ ] **All MVP criteria met**
- [ ] **Performance**: Meets all NFR requirements
  - [ ] Lead processing <7 seconds
  - [ ] Draft generation <15 seconds
  - [ ] Dashboard loads <1 second
- [ ] **Security**:
  - [ ] Security review completed
  - [ ] Environment variables properly secured
  - [ ] Database credentials encrypted
  - [ ] HTTPS enabled for dashboard
  - [ ] API authentication working
- [ ] **Reliability**:
  - [ ] Backup and recovery tested
  - [ ] Database backups running automatically
  - [ ] Error handling tested for edge cases
  - [ ] Email connection failures handled gracefully
- [ ] **Monitoring**:
  - [ ] Health check endpoints operational
  - [ ] Error logging and alerting configured
  - [ ] Performance metrics tracked
- [ ] **Data Quality**:
  - [ ] Manual review of first 50 leads shows >90% accuracy
  - [ ] Draft approval rate >70%
  - [ ] RAG relevance >85%
- [ ] **User Acceptance**:
  - [ ] User training completed
  - [ ] User feedback collected and addressed
  - [ ] Workflow optimized based on user input
- [ ] **Stability**: 30-day stability test passed without major issues

---

## 15. Sign-off

**Prepared by:** Claude AI Assistant
**Date:** October 20, 2025
**Document Version:** 2.0
**Company:** NutriCraft Labs

**Approval:**
- [ ] Product Owner / Business Lead
- [ ] Technical Lead / CTO
- [ ] Security Review
- [ ] Operations Team
- [ ] Knowledge Base/Content Team

---

## Appendix A: Key Architecture Decisions

### Decision 1: Multi-Agent vs Single-Agent
**Chosen**: Multi-agent architecture (Extraction, Response, Analytics)
**Rationale**:
- Separation of concerns for better maintainability
- Each agent can be optimized independently
- Easier to test and debug specialized functionality
- Allows parallel development of agents
- Supports progressive automation (can auto-approve by agent type)

### Decision 2: Database Choice
**Chosen**: PostgreSQL with pgvector extension
**Rationale**:
- Production-ready relational database with ACID guarantees
- Native vector search support via pgvector for RAG system
- Excellent performance for analytical queries
- Strong ecosystem and tooling
- Scalable to millions of records and embeddings
- Superior to SQLite for multi-user web dashboard
- Supports advanced features (JSON columns, full-text search, array types)

### Decision 3: RAG Implementation
**Chosen**: Document-based RAG with pgvector (not web crawling)
**Rationale**:
- Full control over knowledge base content and versioning
- Predictable and auditable information sources
- No dependency on website availability or structure changes
- Easier to ensure accuracy and compliance
- Lower complexity than hybrid document + web approach
- Documents can be reviewed and approved before ingestion

### Decision 4: Approval Interface
**Chosen**: Web-based dashboard (React + FastAPI)
**Rationale**:
- Better user experience than CLI
- Accessible from any device/location
- Supports rich interactions (inline editing, charts, filters)
- Enables team collaboration (multiple reviewers)
- Professional appearance for business tool
- Easier to add future features (mobile support, notifications)
- Industry standard for business applications

### Decision 5: Email Protocol
**Chosen**: IMAP/SMTP via Email MCP Server
**Rationale**:
- Standard protocols, provider-agnostic
- Secure TLS/SSL connections
- Works with any email provider
- MCP abstraction simplifies integration
- Reliable and well-tested

### Decision 6: Background Job Processing
**Chosen**: Celery with Redis
**Rationale**:
- Prevents web interface blocking during email processing
- Enables scheduled tasks (analytics snapshots)
- Proven, production-ready solution
- Good monitoring and debugging tools
- Supports task retries and error handling
- Scalable for future growth

---

## Appendix B: Sample Configuration

### config.yaml
```yaml
# Supplement Lead Intelligence System Configuration

email:
  provider: gmail  # or outlook, custom
  check_interval: 60  # seconds (check every minute)
  max_emails_per_check: 10
  mark_as_read: true
  archive_after_processing: false

database:
  host: localhost  # or postgres service name in Docker
  port: 5432
  name: supplement_leads
  user: ${DB_USER}  # from environment
  password: ${DB_PASSWORD}  # from environment
  pool_size: 10
  max_overflow: 20
  backup_enabled: true
  backup_frequency: daily
  backup_retention_days: 30

rag:
  embedding_model: claude  # or openai
  embedding_dimensions: 1536
  chunk_size: 512
  chunk_overlap: 50
  top_k_retrieval: 10
  min_similarity_score: 0.7
  knowledge_base_path: ./knowledge/

  document_types:
    - product_catalog
    - pricing
    - certification
    - capability
    - faq

agents:
  extraction:
    product_types:
      - probiotics
      - electrolytes
      - protein
      - greens
      - multivitamin
      - pre-workout
      - post-workout
      - sleep
      - nootropics
      - collagen
      - omega-3
      - amino-acids
      - creatine
      - weight-management
      - detox
      - energy
      - immunity
      - joint-health

    certifications:
      - organic
      - non-gmo
      - vegan
      - gluten-free
      - gmp
      - nsf
      - kosher
      - halal
      - third-party-tested

    lead_quality_factors:
      - completeness
      - specificity
      - business_readiness
      - budget_signals
      - volume_indicators

  response:
    tone: professional_b2b
    max_draft_length: 600  # words
    require_approval: true  # Always require approval initially
    min_confidence_for_auto_approval: 9.5  # Future use
    include_source_attribution: true

  analytics:
    snapshot_frequency: daily
    retention_days: 730  # 2 years
    trending_threshold: 0.2  # 20% increase = trending

celery:
  broker_url: redis://localhost:6379/0
  result_backend: redis://localhost:6379/0
  task_serializer: json
  result_serializer: json
  timezone: America/New_York
  enable_utc: true

api:
  host: 0.0.0.0
  port: 8000
  cors_origins:
    - http://localhost:3000  # React dev server
    - https://yourdomain.com
  rate_limit: 100/minute

dashboard:
  items_per_page: 20
  auto_refresh_interval: 30  # seconds
  max_export_rows: 10000

logging:
  level: INFO
  file: ./logs/system.log
  max_size_mb: 100
  backup_count: 10
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

monitoring:
  health_check_enabled: true
  metrics_enabled: true
  error_reporting: true  # Sentry integration
```

### .env.example
```bash
# Database
DB_USER=supplement_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=supplement_leads

# Email Configuration
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=contact@nutricraftlabs.com
EMAIL_PASSWORD=your_email_app_password

# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here  # Optional, for embeddings

# Application
SECRET_KEY=your-secret-key-for-jwt-tokens
ENVIRONMENT=production  # or development
DEBUG=false

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional: Error Tracking
SENTRY_DSN=https://your-sentry-dsn-here
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-20 | Claude AI | Initial PRD compilation from planning conversations |
| 2.0 | 2025-10-20 | Claude AI | Major revision for production-ready supplement lead intelligence system:<br>- Changed from SQLite to PostgreSQL with pgvector<br>- Added RAG system with document-based knowledge base<br>- Changed from CLI to web-based dashboard (React + FastAPI)<br>- Specialized for supplement manufacturing lead qualification<br>- Renamed Classification Agent to Extraction Agent<br>- Added supplement-specific data fields and analytics<br>- Updated to 5-week implementation timeline<br>- Added Celery background job processing<br>- Enhanced with progressive automation metrics |

---

**End of Document**