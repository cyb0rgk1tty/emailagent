"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== Lead Schemas ====================

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

    # Thread tracking and relationships
    conversation_id: Optional[int] = None
    parent_lead_id: Optional[int] = None
    is_duplicate: bool = False
    duplicate_of_lead_id: Optional[int] = None
    lead_status: str = "new"

    # Extracted data
    product_type: Optional[List[str]] = None
    specific_ingredients: Optional[List[str]] = None
    delivery_format: Optional[List[str]] = None
    certifications_requested: Optional[List[str]] = None

    # Business intelligence
    estimated_quantity: Optional[str] = None
    timeline_urgency: Optional[str] = None
    budget_indicator: Optional[str] = None
    experience_level: Optional[str] = None
    distribution_channel: Optional[List[str]] = None
    has_existing_brand: Optional[bool] = None

    # Lead scoring
    lead_quality_score: Optional[int] = Field(None, ge=1, le=10)
    response_priority: Optional[str] = None

    # Metadata
    specific_questions: Optional[List[str]] = None
    geographic_region: Optional[str] = None
    extraction_confidence: Optional[float] = None
    internal_notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadUpdate(BaseModel):
    """Schema for updating a lead"""
    internal_notes: Optional[str] = None
    lead_quality_score: Optional[int] = Field(None, ge=1, le=10)
    response_priority: Optional[str] = None


# ==================== Draft Schemas ====================

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

    # Relationship
    lead: Optional["LeadExtracted"] = None

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
    action: str = Field(..., pattern="^(approve|reject|edit|save)$")
    feedback: Optional[str] = None
    edited_content: Optional[str] = None
    edited_subject: Optional[str] = None
    reviewed_by: str


# ==================== Analytics Schemas ====================

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
    pending_drafts: int
    avg_quality_score: float
    approval_rate: float
    leads_by_priority: Dict[str, int]
    leads_by_product_type: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class AnalyticsTrends(BaseModel):
    """Schema for analytics trends"""
    product_trends: List[ProductTypeTrendResponse]
    certification_trends: Dict[str, int]
    ingredient_trends: Dict[str, int]
    quality_distribution: Dict[int, int]


# ==================== Knowledge Base Schemas ====================

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


class DocumentInfo(BaseModel):
    """Schema for document information"""
    document_name: str
    document_type: str
    chunk_count: int
    version: int
    last_updated: datetime
    is_active: bool


# ==================== RAG Schemas ====================

class RAGQuery(BaseModel):
    """Schema for RAG query"""
    query: str
    top_k: int = 10
    document_types: Optional[List[str]] = None
    min_similarity: float = 0.7

    @field_validator('document_types')
    @classmethod
    def validate_document_types(cls, v):
        if v is not None:
            valid_types = {'product_catalog', 'pricing', 'certification', 'capability', 'faq'}
            for doc_type in v:
                if doc_type not in valid_types:
                    raise ValueError(f"Invalid document type: {doc_type}")
        return v


class RAGResult(BaseModel):
    """Schema for RAG result"""
    chunk_text: str
    document_name: str
    document_type: str
    section_title: Optional[str] = None
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


class RAGResponse(BaseModel):
    """Schema for RAG response with multiple results"""
    query: str
    results: List[RAGResult]
    total_results: int


# ==================== Conversation Schemas ====================

class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: int
    thread_subject: str
    participants: List[str]
    initial_message_id: str
    last_message_id: Optional[str] = None
    started_at: datetime
    last_activity_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailMessageResponse(BaseModel):
    """Schema for email message in conversation"""
    id: int
    message_id: str
    conversation_id: int
    lead_id: Optional[int] = None
    direction: str  # 'inbound' or 'outbound'
    message_type: str
    email_headers: Optional[Dict[str, Any]] = None
    sender_email: str
    sender_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None
    subject: Optional[str] = None
    body: str
    is_draft_sent: bool = False
    draft_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Schema for conversation with all messages"""
    conversation: ConversationResponse
    messages: List[EmailMessageResponse]
    total_messages: int
    lead_info: Optional[Dict[str, Any]] = None


class ConversationTimeline(BaseModel):
    """Schema for conversation timeline"""
    conversation_id: int
    lead_id: int
    thread_subject: str
    timeline: List[Dict[str, Any]]
    started_at: datetime
    last_activity_at: datetime


# ==================== Email Schemas ====================

class EmailMessageSimple(BaseModel):
    """Schema for simple email message (legacy)"""
    subject: str
    body: str
    to_email: EmailStr
    from_email: EmailStr
    message_id: str
    received_at: datetime


# ==================== Pagination ====================

class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Health Check ====================

class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    status: str
    environment: str
    database: str
    redis: Optional[str] = None
    timestamp: datetime
