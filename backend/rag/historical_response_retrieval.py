"""
Historical Response Retrieval for RAG
Retrieves similar historical inquiries and human responses as examples
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from models.database import HistoricalResponseExample
from rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class HistoricalResponseRetrieval:
    """Retrieves similar historical responses for RAG"""

    def __init__(self, top_k: int = 3):
        """
        Initialize historical response retrieval

        Args:
            top_k: Number of top similar responses to retrieve
        """
        self.top_k = top_k
        self.embedder = get_embedding_generator()

    async def find_similar_historical_responses(
        self,
        inquiry_data: Dict,
        top_k: Optional[int] = None,
        min_similarity: float = 0.6
    ) -> List[Dict]:
        """
        Find similar historical inquiries and return human responses

        Args:
            inquiry_data: Current inquiry lead data
            top_k: Number of results to return (default: self.top_k)
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            List of similar historical examples with human responses
        """
        k = top_k or self.top_k

        try:
            # Build query from inquiry data
            query_text = self._build_query_from_inquiry(inquiry_data)

            if not query_text:
                logger.warning("Could not build query from inquiry data")
                return []

            # Generate query embedding
            query_embedding = await self.embedder.generate_query_embedding(query_text)

            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []

            async with get_db_session() as session:
                # Perform similarity search using pgvector
                similarity_expr = text("1 - (embedding <=> :query_embedding)")

                query_stmt = (
                    select(
                        HistoricalResponseExample,
                        similarity_expr.label('similarity')
                    )
                    .where(HistoricalResponseExample.is_active == True)
                    .where(HistoricalResponseExample.embedding.isnot(None))
                    .order_by(text("similarity DESC"))
                    .limit(k)
                )

                result = await session.execute(
                    query_stmt,
                    {"query_embedding": str(query_embedding)}
                )

                rows = result.all()

                # Format results
                examples = []
                for row in rows:
                    example, similarity = row

                    # Filter by minimum similarity
                    if similarity < min_similarity:
                        continue

                    examples.append({
                        'inquiry': {
                            'subject': example.inquiry_subject,
                            'body': example.inquiry_body,
                            'sender_email': example.inquiry_sender_email
                        },
                        'your_response': {
                            'subject': example.response_subject,
                            'body': example.response_body,
                            'date': example.response_date
                        },
                        'similarity': float(similarity),
                        'metadata': example.response_metadata,
                        'context': self._generate_context_description(example, inquiry_data)
                    })

                logger.info(f"Found {len(examples)} similar historical responses (similarity >= {min_similarity})")

                return examples

        except Exception as e:
            logger.error(f"Error finding similar historical responses: {e}", exc_info=True)
            return []

    def _build_query_from_inquiry(self, inquiry_data: Dict) -> str:
        """
        Build search query from inquiry data

        Args:
            inquiry_data: Lead data dictionary

        Returns:
            Query string for semantic search
        """
        try:
            query_parts = []

            # Add product types
            product_types = inquiry_data.get('product_type', [])
            if product_types:
                query_parts.extend(product_types)

            # Add delivery formats
            delivery_formats = inquiry_data.get('delivery_format', [])
            if delivery_formats:
                query_parts.extend(delivery_formats)

            # Add certifications
            certifications = inquiry_data.get('certifications_requested', [])
            if certifications:
                query_parts.extend(certifications)

            # Add specific ingredients
            ingredients = inquiry_data.get('specific_ingredients', [])
            if ingredients:
                query_parts.extend(ingredients[:3])  # Limit to top 3

            # Add quantity/timeline if available
            quantity = inquiry_data.get('estimated_quantity')
            if quantity:
                query_parts.append(quantity)

            timeline = inquiry_data.get('timeline_urgency')
            if timeline:
                query_parts.append(timeline)

            # Fallback to body text if no structured data
            if not query_parts:
                body = inquiry_data.get('body', '')
                query_parts.append(body[:500])  # First 500 chars

            query = ' '.join(query_parts)

            logger.debug(f"Built query: {query[:100]}...")

            return query

        except Exception as e:
            logger.error(f"Error building query: {e}")
            return ""

    def _generate_context_description(
        self,
        example: HistoricalResponseExample,
        current_inquiry: Dict
    ) -> str:
        """
        Generate a description of why this example is relevant

        Args:
            example: Historical response example
            current_inquiry: Current inquiry data

        Returns:
            Context description string
        """
        try:
            similarities = []

            # Check product type similarity
            example_products = self._extract_products_from_text(example.inquiry_body or '')
            current_products = current_inquiry.get('product_type', [])

            if example_products and current_products:
                common_products = set(example_products) & set(current_products)
                if common_products:
                    similarities.append(f"both about {', '.join(common_products)}")

            # Check timeline similarity
            if 'urgent' in (example.inquiry_body or '').lower() and current_inquiry.get('timeline_urgency') == 'urgent':
                similarities.append("both urgent inquiries")

            # Check certification similarity
            if 'organic' in (example.inquiry_body or '').lower() and 'organic' in current_inquiry.get('certifications_requested', []):
                similarities.append("both request organic certification")

            # Check MOQ/quantity questions
            if 'moq' in (example.inquiry_body or '').lower() and 'quantity' in (current_inquiry.get('body', '') or '').lower():
                similarities.append("both ask about minimum order quantities")

            if similarities:
                return "Similar: " + "; ".join(similarities)
            else:
                return "Similar inquiry pattern"

        except Exception as e:
            logger.error(f"Error generating context description: {e}")
            return "Similar inquiry"

    def _extract_products_from_text(self, text: str) -> List[str]:
        """Extract product type mentions from text"""
        text_lower = text.lower()
        common_products = [
            'probiotic', 'protein', 'vitamin', 'electrolyte', 'greens',
            'collagen', 'omega', 'creatine', 'pre-workout', 'multivitamin'
        ]

        found_products = [p for p in common_products if p in text_lower]
        return found_products

    async def format_examples_for_llm(
        self,
        examples: List[Dict],
        max_examples: int = 3
    ) -> str:
        """
        Format historical examples for LLM consumption

        Args:
            examples: List of historical example dictionaries
            max_examples: Maximum number of examples to include

        Returns:
            Formatted string for LLM context
        """
        if not examples:
            return "No similar historical examples found."

        examples = examples[:max_examples]

        formatted_parts = []

        for i, example in enumerate(examples, 1):
            inquiry = example['inquiry']
            response = example['your_response']
            similarity = example['similarity']
            context = example['context']

            formatted = f"""
═══════════════════════════════════════════════════════════════
HISTORICAL EXAMPLE #{i} (Similarity: {similarity:.2f})
{context}
───────────────────────────────────────────────────────────────

THEIR INQUIRY:
Subject: {inquiry['subject']}

{inquiry['body'][:500]}{"..." if len(inquiry['body']) > 500 else ""}

───────────────────────────────────────────────────────────────

YOUR ACTUAL RESPONSE:

{response['body']}

═══════════════════════════════════════════════════════════════
"""
            formatted_parts.append(formatted)

        header = f"""
📚 FOUND {len(examples)} SIMILAR PAST INQUIRIES WITH YOUR RESPONSES

Use these examples to understand your writing style and how you handle similar inquiries.
Adapt the tone, structure, and approach while addressing the current inquiry's specific needs.

"""

        return header + "\n".join(formatted_parts)

    async def get_count(self) -> int:
        """
        Get count of active historical response examples

        Returns:
            Number of active examples
        """
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(HistoricalResponseExample).where(
                        HistoricalResponseExample.is_active == True
                    )
                )
                examples = result.scalars().all()
                return len(examples)

        except Exception as e:
            logger.error(f"Error getting historical response count: {e}")
            return 0


# Singleton instance
_retrieval = None


def get_historical_response_retrieval(top_k: int = 3) -> HistoricalResponseRetrieval:
    """
    Get historical response retrieval instance

    Args:
        top_k: Number of top results to return

    Returns:
        HistoricalResponseRetrieval instance
    """
    global _retrieval
    if _retrieval is None:
        _retrieval = HistoricalResponseRetrieval(top_k=top_k)
    return _retrieval
