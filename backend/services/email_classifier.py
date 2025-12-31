"""
Email Classifier Service
Classifies incoming emails as: new_inquiry, reply_to_us, duplicate, follow_up_inquiry
"""
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import Lead, EmailMessage, Conversation
from rag.embeddings import get_embedding_generator

logger = logging.getLogger(__name__)


class EmailClassificationType:
    """Email classification types"""
    NEW_INQUIRY = "new_inquiry"
    REPLY_TO_US = "reply_to_us"
    DUPLICATE = "duplicate"
    FOLLOW_UP_INQUIRY = "follow_up_inquiry"


class EmailClassifier:
    """Service for classifying incoming emails"""

    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize email classifier

        Args:
            similarity_threshold: Threshold for content similarity (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.embeddings_service = get_embedding_generator()

    async def classify_email(
        self,
        email_data: Dict,
        session: AsyncSession
    ) -> Tuple[str, Optional[Dict]]:
        """Classify an incoming email

        Args:
            email_data: Email data dictionary with headers
            session: Database session

        Returns:
            Tuple of (classification_type, metadata_dict)
        """
        headers = email_data.get('email_headers', {})
        message_id = email_data.get('message_id')
        sender_email = email_data.get('sender_email')
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')

        logger.info(f"Classifying email {message_id} from {sender_email}")

        # 1. Check if this is a reply to our sent emails
        is_reply, reply_metadata = await self._is_reply_to_us(headers, session)
        if is_reply:
            logger.info(f"Email {message_id} is a reply to our message")
            return EmailClassificationType.REPLY_TO_US, reply_metadata

        # 2. Check for duplicate content (forwarded emails)
        is_duplicate, duplicate_metadata = await self._is_duplicate_content(
            email_data, session
        )
        if is_duplicate:
            logger.info(f"Email {message_id} is a duplicate")
            return EmailClassificationType.DUPLICATE, duplicate_metadata

        # 3. Check if this is a follow-up from existing sender
        is_follow_up, follow_up_metadata = await self._is_follow_up_inquiry(
            sender_email, subject, body, session
        )
        if is_follow_up:
            logger.info(f"Email {message_id} is a follow-up inquiry")
            return EmailClassificationType.FOLLOW_UP_INQUIRY, follow_up_metadata

        # 4. Default: New inquiry
        logger.info(f"Email {message_id} is a new inquiry")
        return EmailClassificationType.NEW_INQUIRY, None

    async def _is_reply_to_us(
        self,
        headers: Dict,
        session: AsyncSession
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if email is a reply to our sent messages

        Args:
            headers: Email headers dictionary
            session: Database session

        Returns:
            Tuple of (is_reply, metadata)
        """
        try:
            in_reply_to = headers.get('in_reply_to', '')
            references_list = headers.get('references_list', [])

            if not in_reply_to and not references_list:
                return False, None

            # Check if In-Reply-To or any Reference matches our sent messages
            message_ids_to_check = [in_reply_to] + references_list
            message_ids_to_check = [mid for mid in message_ids_to_check if mid]

            if not message_ids_to_check:
                return False, None

            # Query our outbound messages
            result = await session.execute(
                select(EmailMessage).where(
                    and_(
                        EmailMessage.message_id.in_(message_ids_to_check),
                        EmailMessage.direction == 'outbound'
                    )
                )
            )
            outbound_message = result.scalar_one_or_none()

            if outbound_message:
                # This is a reply to our sent email
                metadata = {
                    'original_message_id': outbound_message.message_id,
                    'original_lead_id': outbound_message.lead_id,
                    'conversation_id': outbound_message.conversation_id,
                    'in_reply_to': in_reply_to
                }
                return True, metadata

            return False, None

        except Exception as e:
            logger.error(f"Error checking reply status: {e}")
            return False, None

    async def _is_duplicate_content(
        self,
        email_data: Dict,
        session: AsyncSession,
        lookback_days: int = 30
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if email content is a duplicate (forwarded email)

        Args:
            email_data: Email data dictionary
            session: Database session
            lookback_days: Number of days to look back

        Returns:
            Tuple of (is_duplicate, metadata)
        """
        try:
            sender_email = email_data.get('sender_email')
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')
            headers = email_data.get('email_headers', {})

            # Quick check: Is subject prefixed with Fwd:/Fw:?
            if headers.get('is_likely_forward', False):
                # Strip forward prefix and check for similar content
                subject_clean = self._strip_forward_prefix(subject)
            else:
                subject_clean = subject

            # Look for recent leads with similar content
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

            result = await session.execute(
                select(Lead).where(
                    and_(
                        Lead.received_at >= cutoff_date,
                        Lead.sender_email != sender_email  # Different sender = potential forward
                    )
                ).order_by(Lead.received_at.desc()).limit(100)
            )
            recent_leads = result.scalars().all()

            if not recent_leads:
                return False, None

            # Use content similarity for duplicate detection
            similarity_results = await self._find_similar_content(
                body, [lead.body for lead in recent_leads]
            )

            for idx, similarity in enumerate(similarity_results):
                if similarity >= self.similarity_threshold:
                    original_lead = recent_leads[idx]
                    metadata = {
                        'original_lead_id': original_lead.id,
                        'similarity_score': similarity,
                        'original_sender': original_lead.sender_email,
                        'is_forward': headers.get('is_likely_forward', False)
                    }
                    logger.info(
                        f"Found duplicate: similarity={similarity:.2f} "
                        f"with lead {original_lead.id}"
                    )
                    return True, metadata

            return False, None

        except Exception as e:
            logger.error(f"Error checking duplicate content: {e}")
            return False, None

    async def _is_follow_up_inquiry(
        self,
        sender_email: str,
        subject: str,
        body: str,
        session: AsyncSession,
        lookback_days: int = 90
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if email is a follow-up inquiry from existing contact

        Args:
            sender_email: Sender email address
            subject: Email subject
            body: Email body
            session: Database session
            lookback_days: Number of days to look back

        Returns:
            Tuple of (is_follow_up, metadata)
        """
        try:
            # Check for previous leads from this sender
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

            result = await session.execute(
                select(Lead).where(
                    and_(
                        Lead.sender_email == sender_email,
                        Lead.received_at >= cutoff_date,
                        Lead.is_duplicate == False
                    )
                ).order_by(Lead.received_at.desc()).limit(1)
            )
            previous_lead = result.scalar_one_or_none()

            if previous_lead:
                # Check if content is different enough to be a new inquiry
                if previous_lead.body:
                    similarity_results = await self._find_similar_content(
                        body, [previous_lead.body]
                    )
                    similarity = similarity_results[0] if similarity_results else 0.0

                    # If very similar content, it's likely spam/duplicate
                    if similarity >= self.similarity_threshold:
                        return False, None  # Will be caught by duplicate check

                # This is a follow-up from an existing contact
                metadata = {
                    'parent_lead_id': previous_lead.id,
                    'conversation_id': previous_lead.conversation_id,
                    'days_since_last_contact': (
                        datetime.now(timezone.utc) - previous_lead.received_at
                    ).days
                }
                return True, metadata

            return False, None

        except Exception as e:
            logger.error(f"Error checking follow-up status: {e}")
            return False, None

    async def _find_similar_content(
        self,
        query_text: str,
        candidate_texts: List[str]
    ) -> List[float]:
        """Find content similarity using embeddings

        Args:
            query_text: Query text
            candidate_texts: List of candidate texts to compare

        Returns:
            List of similarity scores (0-1)
        """
        try:
            if not query_text or not candidate_texts:
                return []

            # Generate embedding for query
            query_embedding = await self.embeddings_service.generate_embedding(
                query_text[:1000]  # Limit to first 1000 chars
            )

            # Generate embeddings for candidates
            similarities = []
            for candidate in candidate_texts:
                if not candidate:
                    similarities.append(0.0)
                    continue

                candidate_embedding = await self.embeddings_service.generate_embedding(
                    candidate[:1000]
                )

                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, candidate_embedding)
                similarities.append(similarity)

            return similarities

        except Exception as e:
            logger.error(f"Error calculating content similarity: {e}")
            return [0.0] * len(candidate_texts)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        try:
            import numpy as np

            v1 = np.array(vec1)
            v2 = np.array(vec2)

            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return float(dot_product / (norm1 * norm2))

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def _strip_forward_prefix(self, subject: str) -> str:
        """Strip forward prefix from subject

        Args:
            subject: Email subject

        Returns:
            Cleaned subject
        """
        prefixes = ['fwd:', 'fw:', 'forward:']
        subject_lower = subject.lower().strip()

        for prefix in prefixes:
            if subject_lower.startswith(prefix):
                return subject[len(prefix):].strip()

        return subject


# Singleton instance
_classifier = None


def get_email_classifier() -> EmailClassifier:
    """Get singleton email classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = EmailClassifier()
    return _classifier
