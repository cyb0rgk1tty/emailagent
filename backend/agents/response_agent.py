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
from rag.historical_response_retrieval import get_historical_response_retrieval
from services.response_learning import get_response_style_analyzer
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
        "name": "Claire",
        "title": "Assistant",
        "company": "Nutricraft Labs",
        "email": "claire@nutricraftlabs.com",
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


async def get_dynamic_system_prompt_with_learning(lead_priority: str) -> str:
    """Get system prompt with learned patterns integrated

    Args:
        lead_priority: Priority level (critical, high, medium, low)

    Returns:
        Dynamic system prompt with learned patterns
    """
    base_prompt = get_dynamic_system_prompt(lead_priority)

    # Try to get learned pattern enhancement
    try:
        analyzer = get_response_style_analyzer()
        learned_enhancement = await analyzer.get_learned_system_prompt_enhancement(lead_priority)

        if learned_enhancement:
            return base_prompt + learned_enhancement

    except Exception as e:
        logger.warning(f"Could not load learned patterns: {e}")

    return base_prompt


def get_dynamic_system_prompt(lead_priority: str) -> str:
    """Get system prompt based on lead priority

    Args:
        lead_priority: Priority level (critical, high, medium, low)

    Returns:
        Dynamic system prompt
    """
    base_prompt = """You are Claire, an AI assistant at Nutricraft Labs, an agency that helps individuals, startups and small to medium business launch their own supplement line.

Your role is to write personalized, professional email responses to potential clients.

CRITICAL: You do NOT need to generate a subject line - it will be auto-generated. Only provide the email body content.

IMPORTANT VOICE & POSITIONING:
- When suggesting calls or meetings, make it clear the call will be with one of our co-founders or team members, not with you (Claire, the assistant). Use phrases like "one of our co-founders", "our team", or "our staff".
- Use "we" instead of "I" when referring to company capabilities or information needs
- You are part of the team, not acting alone
- Examples:
  * Good: "We can help...", "We'd need to know...", "Our team specializes..."
  * Bad: "I can help...", "I need to know...", "I specialize..."
- Exception: Signature remains "Claire, Assistant" (your individual role)"""

    if lead_priority == 'critical':
        return base_prompt + """

PRIORITY LEVEL: CRITICAL
High-value lead with urgent needs. Be concise but responsive.
- Acknowledge urgency without repeating their timeline
- Suggest immediate call/meeting with one of our co-founders or team
- Show immediate availability
- Keep under 120 words
"""
    elif lead_priority == 'high':
        return base_prompt + """

PRIORITY LEVEL: HIGH
Qualified lead with clear intent. Be direct and actionable.
- Focus on next steps, not capabilities recap
- Suggest discovery call with one of our team members
- Be concise - NO repetition of their requirements
- Target 100-120 words
"""
    elif lead_priority == 'medium':
        return base_prompt + """

PRIORITY LEVEL: MEDIUM
Standard inquiry. Be helpful and brief.
- Brief capability mention
- Ask 1-2 clarifying questions if needed
- Suggest conversation with our team if appropriate
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


@response_agent.tool
async def get_similar_past_responses(ctx: RunContext[ResponseDeps]) -> str:
    """
    Retrieve similar inquiries from your historical responses as examples.

    This tool finds past inquiries similar to the current one and shows YOUR
    actual responses to help you adapt your writing style and approach.

    Use this tool to:
    - See how you handled similar product inquiries
    - Match your typical response length and tone
    - Understand what information you typically provide
    - Learn your question-asking patterns

    Returns:
        Formatted examples of similar historical inquiries with your responses
    """
    try:
        lead_data = ctx.deps.lead_data

        # Get historical response retrieval service
        retrieval = get_historical_response_retrieval(top_k=3)

        # Find similar historical responses
        examples = await retrieval.find_similar_historical_responses(
            inquiry_data=lead_data,
            min_similarity=0.6
        )

        if not examples:
            return "No similar historical examples found. Proceed with standard approach based on knowledge base."

        # Format examples for LLM
        formatted_examples = await retrieval.format_examples_for_llm(examples, max_examples=3)

        logger.info(f"Retrieved {len(examples)} historical examples for response generation")

        return formatted_examples

    except Exception as e:
        logger.error(f"Error retrieving similar past responses: {e}")
        return "Unable to retrieve historical examples at this time. Proceed with standard approach."


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

    # Subject line check removed - subject is now generated programmatically, not by AI

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
        specific_ingredients = lead_data.get('specific_ingredients') or []
        certifications = lead_data.get('certifications_requested') or []
        delivery_formats = lead_data.get('delivery_format') or []
        estimated_quantity = lead_data.get('estimated_quantity')
        timeline = lead_data.get('timeline_urgency')

        # Build dynamic context - only show fields that have actual values
        context_parts = []

        if product_types:
            context_parts.append(f"Product type: {', '.join(product_types)}")

        if specific_ingredients:
            context_parts.append(f"Specific ingredients: {', '.join(specific_ingredients)}")

        if delivery_formats:
            context_parts.append(f"Delivery format: {', '.join(delivery_formats)}")

        if certifications:
            context_parts.append(f"Certifications requested: {', '.join(certifications)}")

        if estimated_quantity:
            context_parts.append(f"Quantity: {estimated_quantity}")

        if timeline:
            context_parts.append(f"Timeline: {timeline}")

        # If no context available, provide a minimal note
        context_text = "\n".join(context_parts) if context_parts else "The customer is inquiring about supplement manufacturing (details not specified)"

        prompt = f"""Write a concise, professional B2B email response to this inquiry from {lead_data.get('sender_name', 'Customer')}.

CONTEXT (What the customer told us):
{context_text}

IMPORTANT TOOLS TO USE:
1. Use get_similar_past_responses() FIRST to see how YOU handled similar inquiries in the past
2. Use get_comprehensive_context() to retrieve technical details from knowledge base

Learn from your historical responses to match your typical style, tone, and approach.

CRITICAL RULES - MUST FOLLOW:
1. **DO NOT repeat back what the customer already told you** - Use the CONTEXT to understand their needs, but don't echo it back
2. **ASK smart clarifying questions ONLY about critical missing details:**
   - If delivery format is missing: Ask about format preferences (tablets, capsules, softgels, gummies, powders)
   - If quantity is missing: Ask about estimated order size
   - If timeline is missing: Ask about launch timeline
   - **DO NOT ask about certifications** unless they mentioned certifications in their inquiry
   - DO NOT ask overly technical formulation questions - most customers won't know
   - Limit to 1-2 high-value questions maximum
3. **DON'T ask about information already in CONTEXT:**
   - If they specified format, DON'T ask what format they want
   - If they specified quantity, DON'T ask about quantity
   - If they specified timeline, DON'T ask about timeline
   - If they specified certifications, DON'T ask which certifications again
4. **Assume they know what they asked for - move forward with value**
5. Keep response under {settings.MAX_DRAFT_LENGTH} words (strictly enforced)
6. Be direct and actionable - no fluff or preamble

EMAIL STRUCTURE (3 parts only):
1. **Brief greeting** (1 sentence): "Hi [Name],"
2. **Value + Next steps** (2-3 sentences):
   - Brief capability statement relevant to their needs
   - What you need from them OR suggest a call
3. **Call to action** (1 sentence): Clear next step (if suggesting a call, clarify it's with one of our team members, not with you/Claire)

TONE & STYLE:
- Professional but warm B2B
- Confident and knowledgeable
- Direct and concise
- Action-oriented
- Use "we" for company/team actions and needs (e.g., "we can help", "we'd need to know", "our team")
- Avoid "I" when referring to capabilities or information needs
- NO marketing fluff
- NO repetition of their inquiry

FORMATTING RULES:
- Use simple punctuation: periods, commas, semicolons
- NO em dashes (—) or en dashes (–)
- NO emojis or special characters
- Use periods to separate sentences instead of dashes
- Keep formatting clean and professional

SIGNATURE:
- Sign as "Claire, Assistant, {EMAIL_SIGNATURE['company']}"
- Include email: {EMAIL_SIGNATURE['email']}
- IMPORTANT: Add a blank line between "Best regards," and your name

EXAMPLE OF GOOD LENGTH (75-100 words):
"Hi [Name],

We can definitely help with your supplement project. We specialize in [relevant capability] and have worked with clients in [relevant market].

To provide you with accurate timeline and pricing, we'd need to know [1-2 specific details you need]. Would you be available for a brief call with one of our co-founders this week? If so, please leave your availability and i'll book you in.

Best regards,

Claire
Assistant
Nutricraft Labs
claire@nutricraftlabs.com"
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

            # Override system prompt with learned patterns
            enhanced_system_prompt = await get_dynamic_system_prompt_with_learning(priority)
            response_agent._system_prompts = [enhanced_system_prompt]

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

            # ALWAYS generate subject line programmatically (don't trust AI)
            draft_data['subject_line'] = self._generate_subject_line(lead_data)

            logger.info(
                f"Generated draft for {lead_data.get('sender_email')}: "
                f"confidence={draft_data['confidence_score']:.1f}, type={draft_data['response_type']}, "
                f"subject={draft_data['subject_line']}"
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

We're happy to help coordinate a call with one of our team members to discuss your project in detail.

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
