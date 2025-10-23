"""
Extraction Agent - Extracts structured data from lead emails
Uses PydanticAI with OpenRouter for intelligent field extraction
"""
import logging
from typing import Dict, Optional
from pydantic_ai import Agent, RunContext, ModelRetry

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

Extract the following lead information from emails that are already structured:
- Target Markets
- Order Quantity
- Budget
- Timeline
- Project Type

Extract other information that will be provided in Project Details (free form text) by the lead:
- Product types the client is interested in - BE SPECIFIC! Extract the EXACT supplement type mentioned (e.g., "probiotics", "electrolytes", "creatine", "protein powder", "multivitamins", "omega-3", "collagen", "pre-workout", "greens", "ashwagandha", "vitamin-d", etc.). NEVER use generic terms like "supplements" or "dietary-supplements". If they mention multiple specific products, list each one separately. If no specific product is mentioned, use "Unknown".
- Dosage forms the client is interested in (eg: tablets, capsules, gummies, powders, etc.). Use "Unknown" if not specified.
- Product requirements such as certifications, or specific ingredients (eg: halal or vegan products only, plant based only, etc.). Use "Unknown" if not specified.

Extract other importation business intelligence if needed.

For each email, generate a lead quality score

Be precise and conservative - only extract data that is explicitly mentioned.
Use the search_knowledge_base tool to validate product types and certifications.

LEAD SCORING GUIDELINES:
- lead_quality_score (1-10):
  * Detail level (1-3 points): Vague inquiry vs specific requirements
  * Budget signals (1-2 points): Mentions budget/quantity
  * Urgency (1-2 points): Timeline mentioned
  * Brand maturity (1-2 points): Existing brand vs first-time
  * Specificity (1-1 point): Specific product types and certifications

- response_priority:
  * critical: High budget + urgent timeline + specific needs
  * high: Good detail + clear timeline + reasonable budget
  * medium: Some detail + exploring timeline
  * low: Vague inquiry + no timeline + no budget mentioned""",
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
async def validate_extraction(ctx: RunContext[ExtractionDeps], result: LeadExtraction) -> LeadExtraction:
    """Validate extraction output quality

    Args:
        ctx: Run context with dependencies
        result: Extracted lead data

    Returns:
        Validated LeadExtraction

    Raises:
        ModelRetry: If validation fails
    """
    # Check lead quality score
    if result.lead_quality_score < 1 or result.lead_quality_score > 10:
        raise ModelRetry("Lead quality score must be between 1 and 10")

    # Must have at least some extracted data
    if not result.product_type and not result.specific_ingredients:
        raise ModelRetry("Must extract at least product types or specific ingredients")

    # Confidence check
    if result.extraction_confidence < 0 or result.extraction_confidence > 1:
        raise ModelRetry("Extraction confidence must be between 0 and 1")

    # Priority validation
    valid_priorities = ['critical', 'high', 'medium', 'low']
    if result.response_priority not in valid_priorities:
        raise ModelRetry(f"Response priority must be one of: {', '.join(valid_priorities)}")

    logger.info(
        f"✓ Validated extraction: score={result.lead_quality_score}, "
        f"priority={result.response_priority}, confidence={result.extraction_confidence:.2f}"
    )

    return result


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
1. Product types - BE SPECIFIC! Extract exact supplement names (e.g., "probiotics", "collagen", "omega-3") NOT generic terms like "supplements"
2. Specific ingredients mentioned
3. Delivery formats and certifications requested
4. Business intelligence (quantity, timeline, budget, experience)
5. Distribution channels and geographic region
6. Lead quality score (1-10) and response priority
7. Confidence in extraction accuracy (0-1)

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
