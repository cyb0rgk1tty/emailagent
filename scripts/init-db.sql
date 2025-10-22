-- Supplement Lead Intelligence System - Database Schema
-- PostgreSQL 15+ with pgvector extension

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
CREATE INDEX IF NOT EXISTS idx_leads_received ON leads(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_product_type ON leads USING GIN(product_type);
CREATE INDEX IF NOT EXISTS idx_leads_quality ON leads(lead_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_priority ON leads(response_priority);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(sender_email);
CREATE INDEX IF NOT EXISTS idx_leads_processed ON leads(processed_at) WHERE processed_at IS NOT NULL;

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
CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
CREATE INDEX IF NOT EXISTS idx_drafts_pending ON drafts(status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_drafts_lead ON drafts(lead_id);
CREATE INDEX IF NOT EXISTS idx_drafts_created ON drafts(created_at DESC);

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
-- Note: ivfflat index created after data is inserted (requires training data)
-- For now, create basic indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON document_embeddings(document_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_active ON document_embeddings(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_embeddings_document ON document_embeddings(document_name, version);

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
CREATE INDEX IF NOT EXISTS idx_trends_date ON product_type_trends(date DESC);
CREATE INDEX IF NOT EXISTS idx_trends_product ON product_type_trends(product_type);

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
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON analytics_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_period ON analytics_snapshots(period_type);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for leads table
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for document_embeddings table
DROP TRIGGER IF EXISTS update_embeddings_updated_at ON document_embeddings;
CREATE TRIGGER update_embeddings_updated_at
    BEFORE UPDATE ON document_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
-- Uncomment to add test data
/*
INSERT INTO leads (
    message_id,
    sender_email,
    sender_name,
    company_name,
    subject,
    body,
    received_at,
    product_type,
    lead_quality_score,
    response_priority
) VALUES (
    'test-001',
    'john@example.com',
    'John Doe',
    'HealthCo',
    'Inquiry about custom probiotics',
    'Hi, I am interested in manufacturing a custom probiotic supplement...',
    NOW(),
    ARRAY['probiotics'],
    8,
    'high'
) ON CONFLICT (message_id) DO NOTHING;
*/
