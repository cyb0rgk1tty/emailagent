"""
Response Agent - Generates draft email responses using RAG
Uses PydanticAI with OpenRouter for intelligent response generation
"""
import logging
import json
from pathlib import Path
from typing import Dict, Optional, List
from pydantic_ai import Agent, RunContext, ModelRetry

from models.agent_responses import ResponseDraft
from models.agent_dependencies import ResponseDeps
from services.pydantic_ai_client import get_response_model
from rag import get_semantic_search
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def load_email_signature(signature_name: str = "default") -> Dict[str, str]:
    """Load email signature from configuration file

    Args:
        signature_name: Name of the signature to load (default: "default")

    Returns:
        Dictionary with signature fields (name, title, company, phone, email, website)
    """
    try:
        config_path = Path(__file__).parent.parent / "config" / "email_signature.json"

        if not config_path.exists():
            logger.warning(f"Signature config file not found: {config_path}")
            return _get_fallback_signature()

        with open(config_path, 'r') as f:
            signatures = json.load(f)

        if signature_name not in signatures:
            logger.warning(f"Signature '{signature_name}' not found, using fallback")
            return _get_fallback_signature()

        return signatures[signature_name]

    except Exception as e:
        logger.error(f"Error loading signature config: {e}")
        return _get_fallback_signature()


def _get_fallback_signature() -> Dict[str, str]:
    """Get fallback signature if config file is not available

    Returns:
        Default signature dictionary
    """
    return {
        "name": "Sarah Mitchell",
        "title": "Customer Success Manager",
        "company": "Nutricraft Labs",
        "email": "sarah.mitchell@nutricraftlabs.com",
        "website": "nutricraftlabs.com"
    }


def format_email_signature(signature: Dict[str, str]) -> str:
    """Format signature dictionary into email signature text

    Args:
        signature: Signature dictionary with fields

    Returns:
        Formatted signature string
    """
    lines = [
        f"{signature['name']}",
        f"{signature['title']}",
        f"{signature['company']}",
        f"{signature['email']}"
    ]

    return "\n".join(lines)


def get_dynamic_system_prompt(lead_priority: str) -> str:
    """Get system prompt based on lead priority

    Args:
        lead_priority: Priority level (critical, high, medium, low)

    Returns:
        Dynamic system prompt
    """
    base_prompt = """You are a professional B2B sales representative for Nutricraft Labs, an agency that helps individuals, startups and small to medium business launch their own supplement line.

Your role is to write personalized, professional email responses to potential clients."""

    if lead_priority == 'critical':
        return base_prompt + """

PRIORITY LEVEL: CRITICAL
High-value lead with urgent needs. Be concise but responsive.
- Acknowledge urgency without repeating their timeline
- Suggest immediate call/meeting
- Show immediate availability
- Keep under 120 words
"""
    elif lead_priority == 'high':
        return base_prompt + """

PRIORITY LEVEL: HIGH
Qualified lead with clear intent. Be direct and actionable.
- Focus on next steps, not capabilities recap
- Suggest discovery call
- Be concise - NO repetition of their requirements
- Target 100-120 words
"""
    elif lead_priority == 'medium':
        return base_prompt + """

PRIORITY LEVEL: MEDIUM
Standard inquiry. Be helpful and brief.
- Brief capability mention
- Ask 1-2 clarifying questions if needed
- Suggest conversation
- Target 80-100 words
"""
    else:  # low
        return base_prompt + """

PRIORITY LEVEL: LOW
General inquiry. Be friendly and concise.
- Quick capability statement
- Ask what they're looking for
- Keep it short and simple
- Target 60-80 words
"""


# Load email signature from config
EMAIL_SIGNATURE = load_email_signature()
logger.info(f"Loaded email signature for {EMAIL_SIGNATURE['name']}")

# Initialize PydanticAI agent
response_agent = Agent[ResponseDeps, ResponseDraft](
    model=get_response_model(),
    output_type=ResponseDraft,
    deps_type=ResponseDeps,
    system_prompt=get_dynamic_system_prompt('medium'),  # Default, will be overridden at runtime
    retries=2,
)


@response_agent.tool
async def search_knowledge_base(ctx: RunContext[ResponseDeps], query: str, document_type: Optional[str] = None) -> str:
    """Search the knowledge base for relevant information

    Args:
        query: Search query (e.g., "probiotics MOQ pricing")
        document_type: Optional document type filter (e.g., "capability", "pricing")

    Returns:
        Relevant context from knowledge base
    """
    try:
        search = get_semantic_search()

        # Perform similarity search
        results = await search.similarity_search(
            query=query,
            top_k=5,
            min_similarity=0.5,
            document_type=document_type
        )

        if not results:
            return "No relevant information found in knowledge base for this query."

        # Format results
        formatted = []
        for r in results:
            formatted.append(
                f"Source: {r['document_name']} (Section: {r.get('section_title', 'N/A')})\n"
                f"Content: {r['text']}\n"
                f"Relevance: {r['similarity']:.2f}"
            )

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return f"Error searching knowledge base: {str(e)}"


@response_agent.tool
async def get_comprehensive_context(ctx: RunContext[ResponseDeps]) -> str:
    """Get comprehensive context for the lead based on their needs

    Uses the lead data from context to build targeted search query.

    Returns:
        Formatted comprehensive context
    """
    try:
        lead_data = ctx.deps.lead_data

        # Build search query from extracted data
        query_parts = []

        if lead_data.get('product_type'):
            query_parts.extend(lead_data['product_type'])

        if lead_data.get('certifications_requested'):
            query_parts.extend(lead_data['certifications_requested'])

        if lead_data.get('delivery_format'):
            query_parts.extend(lead_data['delivery_format'])

        # Add generic supplement query
        query_parts.append("manufacturing capabilities MOQ pricing")

        query = " ".join(query_parts)

        # Get relevant context from knowledge base
        search = get_semantic_search()
        rag_context = await search.get_context_for_query(
            query=query,
            max_tokens=3000
        )

        logger.info(f"Retrieved comprehensive RAG context for lead")
        return rag_context

    except Exception as e:
        logger.error(f"Error getting comprehensive context: {e}")
        return "Unable to retrieve comprehensive context at this time."


@response_agent.output_validator
async def validate_response_draft(ctx: RunContext[ResponseDeps], result: ResponseDraft) -> ResponseDraft:
    """Validate response draft quality

    Args:
        ctx: Run context with dependencies
        result: Generated response draft

    Returns:
        Validated ResponseDraft

    Raises:
        ModelRetry: If validation fails
    """
    # Check confidence score range
    if result.confidence_score < 0 or result.confidence_score > 10:
        raise ModelRetry("Confidence score must be between 0 and 10")

    # Check subject line
    if len(result.subject_line) < 5:
        raise ModelRetry("Subject line must be at least 5 characters")

    # Check draft content length (character count)
    if len(result.draft_content) < 100:
        raise ModelRetry("Draft content must be at least 100 characters")

    if len(result.draft_content) > 15000:
        raise ModelRetry("Draft content must be less than 15000 characters")

    # Check word count (enforce MAX_DRAFT_LENGTH)
    word_count = len(result.draft_content.split())
    max_words = settings.MAX_DRAFT_LENGTH
    if word_count > max_words:
        raise ModelRetry(f"Draft is too long ({word_count} words). Must be under {max_words} words. Be more concise.")

    # Check for em dashes and en dashes
    if '—' in result.draft_content or '–' in result.draft_content:
        raise ModelRetry("Do not use em dashes (—) or en dashes (–). Use periods or commas instead.")

    # Check for emojis (basic check for common emoji unicode ranges)
    import re
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    if emoji_pattern.search(result.draft_content):
        raise ModelRetry("Do not use emojis in professional email drafts.")

    # Check that draft includes proper email format
    if not any(greeting in result.draft_content.lower() for greeting in ['dear', 'hello', 'hi', 'greetings']):
        raise ModelRetry("Draft must include a proper greeting")

    # Check for signature
    if 'nutricraftlabs.com' not in result.draft_content.lower() and 'nutricraft labs' not in result.draft_content.lower():
        raise ModelRetry("Draft must include company signature")

    # Warn if confidence is low
    if result.confidence_score < 5.0:
        logger.warning(f"Low confidence score: {result.confidence_score}")
        if 'low_confidence' not in result.flags:
            result.flags.append('low_confidence')

    logger.info(
        f"✓ Validated response draft: confidence={result.confidence_score:.1f}, "
        f"type={result.response_type}, flags={len(result.flags)}"
    )

    return result


class ResponseAgentWrapper:
    """Wrapper for response agent to maintain compatibility with existing code"""

    def __init__(self):
        """Initialize response agent"""
        logger.info("Initialized PydanticAI Response Agent with OpenRouter")

    async def build_response_prompt(self, lead_data: Dict, rag_context: str) -> str:
        """Build response generation prompt (for compatibility)

        Args:
            lead_data: Extracted lead data
            rag_context: Relevant context from knowledge base

        Returns:
            Response generation prompt
        """
        product_types = lead_data.get('product_type') or []
        certifications = lead_data.get('certifications_requested') or []
        delivery_formats = lead_data.get('delivery_format') or []
        questions = lead_data.get('specific_questions') or []

        prompt = f"""Write a concise, professional B2B email response to this inquiry from {lead_data.get('sender_name', 'Customer')}.

CONTEXT (DO NOT REPEAT IN EMAIL):
The customer is interested in: {', '.join(product_types) if product_types else 'supplement manufacturing'}
They need quantity: {lead_data.get('estimated_quantity', 'unspecified')}
Timeline: {lead_data.get('timeline_urgency', 'exploring')}

Use the get_comprehensive_context tool to retrieve relevant knowledge base information for accurate technical details.

CRITICAL RULES - MUST FOLLOW:
1. **DO NOT repeat back what the customer already told you**
2. **DO NOT echo their requirements or specifications**
3. **Assume they know what they asked for - move forward with value**
4. Keep response under {settings.MAX_DRAFT_LENGTH} words (strictly enforced)
5. Be direct and actionable - no fluff or preamble

EMAIL STRUCTURE (3 parts only):
1. **Brief greeting** (1 sentence): "Hi [Name],"
2. **Value + Next steps** (2-3 sentences):
   - Brief capability statement relevant to their needs
   - What you need from them OR suggest a call
3. **Call to action** (1 sentence): Clear next step

TONE & STYLE:
- Professional but warm B2B
- Confident and knowledgeable
- Direct and concise
- Action-oriented
- NO marketing fluff
- NO repetition of their inquiry

FORMATTING RULES:
- Use simple punctuation: periods, commas, semicolons
- NO em dashes (—) or en dashes (–)
- NO emojis or special characters
- Use periods to separate sentences instead of dashes
- Keep formatting clean and professional

SIGNATURE:
- Sign as "{EMAIL_SIGNATURE['name']}, {EMAIL_SIGNATURE['title']}, {EMAIL_SIGNATURE['company']}"
- Include email: {EMAIL_SIGNATURE['email']}

EXAMPLE OF GOOD LENGTH (75-100 words):
"Hi [Name],

We can definitely help with your supplement project. We specialize in [relevant capability] and have worked with clients in [relevant market].

To provide you with accurate timeline and pricing, I'd like to understand [1-2 specific details you need]. Would you be available for a brief call this week?

Best regards,
[Signature]"
"""
        return prompt

    async def generate_response(self, lead_data: Dict) -> Optional[Dict]:
        """Generate email draft response for a lead

        Args:
            lead_data: Extracted lead data with email content

        Returns:
            Draft data dictionary with subject and content
        """
        try:
            # Build prompt
            prompt = await self.build_response_prompt(lead_data, "")

            # Get lead priority for dynamic system prompt
            priority = lead_data.get('response_priority', 'medium')

            # Override system prompt based on priority
            response_agent._system_prompts = [get_dynamic_system_prompt(priority)]

            # Create dependencies
            deps = ResponseDeps(
                config=settings,
                lead_data=lead_data,
                email_content=lead_data.get('body', '')
            )

            # Run agent
            result = await response_agent.run(prompt, deps=deps)

            # Convert to dictionary for compatibility
            draft_data = result.output.model_dump()

            logger.info(
                f"Generated draft for {lead_data.get('sender_email')}: "
                f"confidence={draft_data['confidence_score']:.1f}, type={draft_data['response_type']}"
            )

            return draft_data

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            # Fall back to simple response
            return self._fallback_response(lead_data)

    def _generate_subject_line(self, lead_data: Dict) -> str:
        """Generate appropriate subject line

        Args:
            lead_data: Lead data

        Returns:
            Subject line
        """
        original_subject = lead_data.get('subject', '')

        if original_subject.lower().startswith('re:'):
            return original_subject

        return f"Re: {original_subject}" if original_subject else "Re: Supplement Manufacturing Inquiry"

    def _fallback_response(self, lead_data: Dict) -> Dict:
        """Generate simple fallback response

        Args:
            lead_data: Lead data

        Returns:
            Basic draft data
        """
        logger.warning("Using fallback response generation")

        sender_name = lead_data.get('sender_name', 'there')
        products = lead_data.get('product_type', [])

        product_mention = f"{products[0]} supplements" if products else "supplement products"

        content = f"""Dear {sender_name},

Thank you for reaching out to {EMAIL_SIGNATURE['company']} regarding {product_mention}.

We'd love to learn more about your specific needs and provide you with detailed information about our manufacturing capabilities, certifications, and pricing.

Could you please provide some additional details about your project? Specifically:
- Desired product format (capsules, powder, gummies, etc.)
- Estimated order quantity
- Any specific certifications required
- Timeline for launch

I'm happy to schedule a call to discuss your project in detail.

Best regards,
{EMAIL_SIGNATURE['name']}
{EMAIL_SIGNATURE['title']}
{EMAIL_SIGNATURE['company']}
{EMAIL_SIGNATURE['email']}"""

        return {
            'subject_line': self._generate_subject_line(lead_data),
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
