"""
SQLAlchemy ORM models for the Supplement Lead Intelligence System
"""
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Boolean, Float,
    ForeignKey, ARRAY, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from database import Base


class Conversation(Base):
    """Conversation model - groups related emails into threads"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)

    # Thread identification
    thread_subject = Column(Text, nullable=False)
    participants = Column(ARRAY(String), nullable=False)  # List of email addresses

    # Thread metadata
    initial_message_id = Column(String, unique=True, nullable=False, index=True)
    last_message_id = Column(String, index=True)

    # Timestamps
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    last_activity_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Conversation(id={self.id}, subject={self.thread_subject[:50]})>"


class EmailMessage(Base):
    """EmailMessage model - stores all email messages (inbound and outbound)"""
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Message identification
    message_id = Column(String, unique=True, nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), index=True)

    # Message direction and type
    direction = Column(String, nullable=False, index=True)  # 'inbound' or 'outbound'
    message_type = Column(String, default="email")  # 'email', 'note', 'system'

    # Email headers (RFC 5322)
    email_headers = Column(JSONB)  # Stores In-Reply-To, References, etc.

    # Content
    sender_email = Column(String, nullable=False, index=True)
    sender_name = Column(String)
    recipient_email = Column(String)
    recipient_name = Column(String)
    subject = Column(Text)
    body = Column(Text, nullable=False)

    # Metadata
    is_draft_sent = Column(Boolean, default=False)  # True if this is a sent draft
    draft_id = Column(Integer, ForeignKey("drafts.id", ondelete="SET NULL"))

    # Timestamps
    sent_at = Column(TIMESTAMP(timezone=True), index=True)
    received_at = Column(TIMESTAMP(timezone=True), index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "direction IN ('inbound', 'outbound')",
            name='valid_direction'
        ),
        CheckConstraint(
            "message_type IN ('email', 'note', 'system')",
            name='valid_message_type'
        ),
    )

    def __repr__(self):
        return f"<EmailMessage(id={self.id}, direction={self.direction}, from={self.sender_email})>"


class Lead(Base):
    """Lead model - stores contact form submissions and extracted data"""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, nullable=False)

    # Thread tracking and relationships
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"), index=True)
    parent_lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"), index=True)

    # Duplicate detection
    is_duplicate = Column(Boolean, default=False, index=True)
    duplicate_of_lead_id = Column(Integer, ForeignKey("leads.id", ondelete="SET NULL"))

    # Lead lifecycle status
    lead_status = Column(String, nullable=False, default="new", index=True)

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

    # Relationships
    drafts = relationship("Draft", back_populates="lead")

    __table_args__ = (
        CheckConstraint('lead_quality_score >= 1 AND lead_quality_score <= 10', name='valid_quality_score'),
        CheckConstraint("response_priority IN ('critical', 'high', 'medium', 'low')", name='valid_priority'),
        CheckConstraint(
            "lead_status IN ('new', 'responded', 'customer_replied', 'conversation_active', 'closed')",
            name='valid_lead_status'
        ),
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

    # Relationships
    lead = relationship("Lead", back_populates="drafts")

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
