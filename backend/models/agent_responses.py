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
        """Validate response priority is one of the allowed values"""
        valid = ['critical', 'high', 'medium', 'low']
        if v not in valid:
            raise ValueError(f"Priority must be one of {valid}")
        return v

    @field_validator('timeline_urgency')
    @classmethod
    def validate_timeline(cls, v: Optional[str]) -> Optional[str]:
        """Validate timeline urgency is one of the allowed values"""
        if v is None:
            return v
        valid = ['urgent', 'medium-1-3-months', 'long-term-6-plus-months', 'exploring']
        if v not in valid:
            raise ValueError(f"Timeline must be one of {valid}")
        return v

    @field_validator('budget_indicator')
    @classmethod
    def validate_budget(cls, v: Optional[str]) -> Optional[str]:
        """Validate budget indicator is one of the allowed values"""
        if v is None:
            return v
        valid = ['startup', 'mid-market', 'enterprise']
        if v not in valid:
            raise ValueError(f"Budget indicator must be one of {valid}")
        return v

    @field_validator('experience_level')
    @classmethod
    def validate_experience(cls, v: Optional[str]) -> Optional[str]:
        """Validate experience level is one of the allowed values"""
        if v is None:
            return v
        valid = ['first-time', 'established-brand', 'experienced']
        if v not in valid:
            raise ValueError(f"Experience level must be one of {valid}")
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
        description="Response type: high_priority_detailed, detailed_quote, standard_inquiry, basic_information, fallback"
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
        """Validate response type is one of the allowed values"""
        valid = ['high_priority_detailed', 'detailed_quote', 'standard_inquiry', 'basic_information', 'fallback']
        if v not in valid:
            raise ValueError(f"Response type must be one of {valid}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is one of the allowed values"""
        valid = ['pending', 'approved', 'rejected', 'sent', 'edited']
        if v not in valid:
            raise ValueError(f"Status must be one of {valid}")
        return v

    @field_validator('subject_line')
    @classmethod
    def validate_subject_line(cls, v: str) -> str:
        """Validate subject line is not empty and has reasonable length"""
        if not v or len(v.strip()) < 3:
            raise ValueError("Subject line must be at least 3 characters")
        if len(v) > 200:
            raise ValueError("Subject line must be less than 200 characters")
        return v.strip()

    @field_validator('draft_content')
    @classmethod
    def validate_draft_content(cls, v: str) -> str:
        """Validate draft content is not empty and has reasonable length"""
        if not v or len(v.strip()) < 50:
            raise ValueError("Draft content must be at least 50 characters")
        if len(v) > 10000:
            raise ValueError("Draft content must be less than 10000 characters")
        return v.strip()


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
    related_data: Optional[dict] = Field(
        default=None,
        description="Related data points supporting the insight"
    )

    @field_validator('insight_type')
    @classmethod
    def validate_insight_type(cls, v: str) -> str:
        """Validate insight type is one of the allowed values"""
        valid = ['trend', 'anomaly', 'recommendation']
        if v not in valid:
            raise ValueError(f"Insight type must be one of {valid}")
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty and has reasonable length"""
        if not v or len(v.strip()) < 5:
            raise ValueError("Title must be at least 5 characters")
        if len(v) > 100:
            raise ValueError("Title must be less than 100 characters")
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty"""
        if not v or len(v.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")
        return v.strip()
