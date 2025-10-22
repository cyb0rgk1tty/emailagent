"""
Models package
Contains SQLAlchemy ORM models and Pydantic schemas
"""
from .database import Lead, Draft, DocumentEmbedding, ProductTypeTrend, AnalyticsSnapshot
from . import schemas
from .agent_responses import LeadExtraction, ResponseDraft, AnalyticsInsight
from .agent_dependencies import BaseDeps, ExtractionDeps, ResponseDeps, AnalyticsDeps

__all__ = [
    # Database models
    "Lead",
    "Draft",
    "DocumentEmbedding",
    "ProductTypeTrend",
    "AnalyticsSnapshot",
    # API schemas
    "schemas",
    # Agent response models
    "LeadExtraction",
    "ResponseDraft",
    "AnalyticsInsight",
    # Agent dependency models
    "BaseDeps",
    "ExtractionDeps",
    "ResponseDeps",
    "AnalyticsDeps",
]
