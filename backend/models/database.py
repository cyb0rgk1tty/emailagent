"""
SQLAlchemy ORM models for the Supplement Lead Intelligence System
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Boolean, Float,
    ForeignKey, ARRAY, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base


class Lead(Base):
    """Lead model - stores contact form submissions and extracted data"""
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

    # Supplement-specific data (arrays)
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
        CheckConstraint("response_priority IN ('critical', 'high', 'medium', 'low')", name='valid_priority'),
    )

    def __repr__(self):
        return f"<Lead(id={self.id}, email={self.sender_email}, score={self.lead_quality_score})>"


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

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'sent', 'edited')", name='valid_draft_status'),
        CheckConstraint("customer_sentiment IS NULL OR customer_sentiment IN ('positive', 'neutral', 'negative')", name='valid_sentiment'),
    )

    def __repr__(self):
        return f"<Draft(id={self.id}, lead_id={self.lead_id}, status={self.status})>"


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
    doc_metadata = Column("metadata", JSONB)
    is_active = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "document_type IN ('product_catalog', 'pricing', 'certification', 'capability', 'faq')",
            name='valid_document_type'
        ),
    )

    def __repr__(self):
        return f"<DocumentEmbedding(id={self.id}, doc={self.document_name}, type={self.document_type})>"


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

    def __repr__(self):
        return f"<ProductTypeTrend(product={self.product_type}, date={self.date}, count={self.mention_count})>"


class AnalyticsSnapshot(Base):
    """Analytics snapshots for historical reporting"""
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    period_type = Column(String, nullable=False)
    metrics = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("period_type IN ('daily', 'weekly', 'monthly')", name='valid_period_type'),
    )

    def __repr__(self):
        return f"<AnalyticsSnapshot(date={self.snapshot_date}, type={self.period_type})>"
