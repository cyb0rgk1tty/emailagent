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
