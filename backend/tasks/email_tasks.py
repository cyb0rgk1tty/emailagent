"""
Celery tasks for email processing
Handles email ingestion, extraction, and response generation
"""
import logging
import re
from typing import Dict, List
from datetime import datetime

from sqlalchemy import select

from tasks.celery_app import celery_app
from database import get_db_session
from models.database import Lead, Draft, Conversation, EmailMessage
from agents import get_extraction_agent, get_response_agent, get_analytics_agent
from services.email_service import get_email_service
from services.email_classifier import get_email_classifier, EmailClassificationType
from utils.email_utils import html_to_text

logger = logging.getLogger(__name__)


def strip_html_tags(html_content: str) -> str:
    """Strip HTML tags from email content and extract plain text

    This function now uses the shared html_to_text utility for consistent
    HTML-to-text conversion across the codebase.

    Args:
        html_content: HTML content string

    Returns:
        Plain text content
    """
    return html_to_text(html_content)


@celery_app.task(name='tasks.email_tasks.check_new_emails')
def check_new_emails():
    """Periodic task: Check for new emails and process them"""
    import asyncio

    async def _check():
        logger.info("Checking for new emails...")

        try:
            email_service = get_email_service()

            # Fetch emails from last 7 days (date-based filtering instead of UNSEEN)
            # This captures emails even if they've been marked as read in email client
            # Duplicate detection (by message_id) prevents reprocessing
            new_emails = await email_service.fetch_new_emails(limit=50, since_days=7)

            if not new_emails:
                logger.info("No new emails found")
                return {'status': 'success', 'emails_processed': 0}

            logger.info(f"Found {len(new_emails)} new emails")

            # Process each email
            processed_count = 0

            for email in new_emails:
                try:
                    # Queue processing task
                    process_email.delay(email)
                    processed_count += 1

                except Exception as e:
                    logger.error(f"Error queuing email {email.get('message_id')}: {e}")

            return {
                'status': 'success',
                'emails_found': len(new_emails),
                'emails_queued': processed_count
            }

        except Exception as e:
            logger.error(f"Error checking new emails: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    return asyncio.run(_check())


@celery_app.task(name='tasks.email_tasks.process_email')
def process_email(email_data: Dict):
    """Process a single email through the agent pipeline

    Args:
        email_data: Email data dictionary
    """
    import asyncio

    async def _process():
        message_id = email_data.get('message_id')
        sender_email = email_data.get('sender_email', '')
        logger.info(f"Processing email: {message_id} from {sender_email}")

        try:
            # Filter out internal employee emails (but allow contact form from info@)
            # Contact form submissions come from info@nutricraftlabs.com
            # Internal employee replies come from employee addresses like cyin@nutricraftlabs.com
            if '@' in sender_email:
                sender_lower = sender_email.lower()
                # Skip internal employee emails but allow info@ (contact form)
                if sender_lower.endswith('@nutricraftlabs.com') and not sender_lower.startswith('info@'):
                    logger.info(f"Skipping internal employee email from {sender_email}")
                    return {'status': 'skipped', 'reason': 'internal_email', 'sender': sender_email}

            # Check if already processed
            async with get_db_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(Lead).where(Lead.message_id == message_id)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"Email {message_id} already processed")
                    return {'status': 'skipped', 'reason': 'already_processed'}

            # Step 1: Classify the email
            classifier = get_email_classifier()
            async with get_db_session() as session:
                classification, metadata = await classifier.classify_email(email_data, session)

            logger.info(f"Email classified as: {classification}")

            # Route based on classification
            if classification == EmailClassificationType.REPLY_TO_US:
                return await _process_reply(email_data, metadata)

            elif classification == EmailClassificationType.DUPLICATE:
                return await _process_duplicate(email_data, metadata)

            elif classification == EmailClassificationType.FOLLOW_UP_INQUIRY:
                return await _process_follow_up(email_data, metadata)

            else:  # NEW_INQUIRY
                return await _process_new_inquiry(email_data)

        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e), 'message_id': message_id}

    async def _process_new_inquiry(email_data: Dict) -> Dict:
        """Process a new inquiry email"""
        message_id = email_data.get('message_id')

        # Strip HTML from body if present
        body = email_data.get('body', '')
        cleaned_body = strip_html_tags(body)
        email_data['body'] = cleaned_body

        # Step 1: Extract data
        extraction_agent = get_extraction_agent()
        extracted_data = await extraction_agent.extract_from_email(email_data)

        if not extracted_data:
            logger.error(f"Failed to extract data from email {message_id}")
            return {'status': 'error', 'step': 'extraction'}

        logger.info(
            f"Extracted data: score={extracted_data.get('lead_quality_score')}, "
            f"priority={extracted_data.get('response_priority')}"
        )

        # Step 2: Create conversation and save lead
        async with get_db_session() as session:
            # Create conversation
            conversation = Conversation(
                thread_subject=email_data.get('subject', ''),
                participants=[email_data.get('sender_email')],
                initial_message_id=message_id,
                last_message_id=message_id,
                started_at=email_data.get('received_at') or datetime.utcnow(),
                last_activity_at=email_data.get('received_at') or datetime.utcnow()
            )
            session.add(conversation)
            await session.flush()

            conversation_id = conversation.id

            # Create lead
            lead = Lead(
                message_id=message_id,
                conversation_id=conversation_id,
                lead_status='new',
                sender_email=email_data.get('sender_email'),
                sender_name=email_data.get('sender_name'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                received_at=email_data.get('received_at') or datetime.utcnow(),
                processed_at=datetime.utcnow(),

                # Extracted data
                product_type=extracted_data.get('product_type'),
                specific_ingredients=extracted_data.get('specific_ingredients'),
                delivery_format=extracted_data.get('delivery_format'),
                certifications_requested=extracted_data.get('certifications_requested'),

                estimated_quantity=extracted_data.get('estimated_quantity'),
                timeline_urgency=extracted_data.get('timeline_urgency'),
                budget_indicator=extracted_data.get('budget_indicator'),
                experience_level=extracted_data.get('experience_level'),
                distribution_channel=extracted_data.get('distribution_channel'),
                has_existing_brand=extracted_data.get('has_existing_brand'),

                lead_quality_score=extracted_data.get('lead_quality_score'),
                response_priority=extracted_data.get('response_priority'),

                specific_questions=extracted_data.get('specific_questions'),
                geographic_region=extracted_data.get('geographic_region'),
                extraction_confidence=extracted_data.get('extraction_confidence'),
            )
            session.add(lead)
            await session.flush()

            lead_id = lead.id

            # Create email message record
            email_message = EmailMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                lead_id=lead_id,
                direction='inbound',
                message_type='email',
                email_headers=email_data.get('email_headers', {}),
                sender_email=email_data.get('sender_email'),
                sender_name=email_data.get('sender_name'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                received_at=email_data.get('received_at') or datetime.utcnow()
            )
            session.add(email_message)

            await session.commit()

        logger.info(f"Saved lead {lead_id} and conversation {conversation_id}")

        # Check if email is spam/advertisement - skip draft generation if so
        if extracted_data.get('is_spam_or_advertisement', False):
            spam_reason = extracted_data.get('spam_reason', 'No reason provided')
            logger.info(f"Email classified as spam/advertisement: {spam_reason}")

            # Update lead status to spam
            async with get_db_session() as session:
                result = await session.execute(
                    select(Lead).where(Lead.id == lead_id)
                )
                lead = result.scalar_one()
                lead.lead_status = 'spam'
                lead.internal_notes = f"Spam/Advertisement: {spam_reason}"
                await session.commit()

            logger.info(f"✅ Processed spam/advertisement email {message_id} - no draft generated")

            return {
                'status': 'success',
                'classification': 'spam',
                'message_id': message_id,
                'lead_id': lead_id,
                'conversation_id': conversation_id,
                'spam_reason': spam_reason,
            }

        # Step 3: Generate response
        response_agent = get_response_agent()
        draft_data = await response_agent.generate_response(extracted_data)

        if not draft_data:
            logger.error(f"Failed to generate response for lead {lead_id}")
            return {'status': 'error', 'step': 'response_generation', 'lead_id': lead_id}

        logger.info(f"Generated draft (confidence: {draft_data.get('confidence_score')})")

        # Step 4: Save draft and update lead status
        async with get_db_session() as session:
            draft = Draft(
                lead_id=lead_id,
                subject_line=draft_data.get('subject_line'),
                draft_content=draft_data.get('draft_content'),
                status=draft_data.get('status', 'pending'),
                response_type=draft_data.get('response_type'),
                confidence_score=draft_data.get('confidence_score'),
                flags=draft_data.get('flags'),
                rag_sources=draft_data.get('rag_sources'),
            )
            session.add(draft)

            # Update lead status
            result = await session.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one()
            lead.lead_status = 'responded'

            await session.commit()
            draft_id = draft.id

        logger.info(f"Saved draft {draft_id}")

        # Step 5: Update analytics
        analytics_agent = get_analytics_agent()
        await analytics_agent.update_product_trends_from_lead(lead_id)

        logger.info(f"✅ Successfully processed new inquiry {message_id}")

        return {
            'status': 'success',
            'classification': 'new_inquiry',
            'message_id': message_id,
            'lead_id': lead_id,
            'conversation_id': conversation_id,
            'draft_id': draft_id,
            'lead_quality_score': extracted_data.get('lead_quality_score'),
            'response_priority': extracted_data.get('response_priority'),
        }

    async def _process_reply(email_data: Dict, metadata: Dict) -> Dict:
        """Process a reply to our sent email"""
        message_id = email_data.get('message_id')
        conversation_id = metadata.get('conversation_id')
        original_lead_id = metadata.get('original_lead_id')

        # Strip HTML from body if present
        body = email_data.get('body', '')
        cleaned_body = strip_html_tags(body)

        async with get_db_session() as session:
            # Add message to conversation
            email_message = EmailMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                lead_id=original_lead_id,
                direction='inbound',
                message_type='email',
                email_headers=email_data.get('email_headers', {}),
                sender_email=email_data.get('sender_email'),
                sender_name=email_data.get('sender_name'),
                subject=email_data.get('subject'),
                body=cleaned_body,
                received_at=email_data.get('received_at') or datetime.utcnow()
            )
            session.add(email_message)

            # Update conversation
            from sqlalchemy import select
            result = await session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.last_message_id = message_id
                conversation.last_activity_at = datetime.utcnow()

            # Update lead status
            result = await session.execute(
                select(Lead).where(Lead.id == original_lead_id)
            )
            lead = result.scalar_one_or_none()
            if lead:
                lead.lead_status = 'customer_replied'
                lead.updated_at = datetime.utcnow()

            await session.commit()

        logger.info(f"✅ Processed reply {message_id} for lead {original_lead_id}")

        return {
            'status': 'success',
            'classification': 'reply_to_us',
            'message_id': message_id,
            'lead_id': original_lead_id,
            'conversation_id': conversation_id
        }

    async def _process_duplicate(email_data: Dict, metadata: Dict) -> Dict:
        """Process a duplicate/forwarded email"""
        message_id = email_data.get('message_id')
        original_lead_id = metadata.get('original_lead_id')

        # Strip HTML from body if present
        body = email_data.get('body', '')
        cleaned_body = strip_html_tags(body)

        async with get_db_session() as session:
            # Create duplicate lead entry
            lead = Lead(
                message_id=message_id,
                is_duplicate=True,
                duplicate_of_lead_id=original_lead_id,
                lead_status='closed',
                sender_email=email_data.get('sender_email'),
                sender_name=email_data.get('sender_name'),
                subject=email_data.get('subject'),
                body=cleaned_body,
                received_at=email_data.get('received_at') or datetime.utcnow(),
                processed_at=datetime.utcnow()
            )
            session.add(lead)
            await session.commit()

        logger.info(f"✅ Marked email {message_id} as duplicate of lead {original_lead_id}")

        return {
            'status': 'success',
            'classification': 'duplicate',
            'message_id': message_id,
            'original_lead_id': original_lead_id,
            'similarity_score': metadata.get('similarity_score')
        }

    async def _process_follow_up(email_data: Dict, metadata: Dict) -> Dict:
        """Process a follow-up inquiry from existing contact"""
        message_id = email_data.get('message_id')
        parent_lead_id = metadata.get('parent_lead_id')
        parent_conversation_id = metadata.get('conversation_id')

        # Strip HTML from body if present
        body = email_data.get('body', '')
        cleaned_body = strip_html_tags(body)
        email_data['body'] = cleaned_body

        # Extract data for new lead
        extraction_agent = get_extraction_agent()
        extracted_data = await extraction_agent.extract_from_email(email_data)

        if not extracted_data:
            logger.error(f"Failed to extract data from follow-up email {message_id}")
            return {'status': 'error', 'step': 'extraction'}

        async with get_db_session() as session:
            # Determine if we should create new conversation or continue existing
            conversation_id = parent_conversation_id

            if not conversation_id:
                # Create new conversation
                conversation = Conversation(
                    thread_subject=email_data.get('subject', ''),
                    participants=[email_data.get('sender_email')],
                    initial_message_id=message_id,
                    last_message_id=message_id,
                    started_at=email_data.get('received_at') or datetime.utcnow(),
                    last_activity_at=email_data.get('received_at') or datetime.utcnow()
                )
                session.add(conversation)
                await session.flush()
                conversation_id = conversation.id
            else:
                # Update existing conversation
                from sqlalchemy import select
                result = await session.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    conversation.last_message_id = message_id
                    conversation.last_activity_at = datetime.utcnow()

            # Create new lead linked to parent
            lead = Lead(
                message_id=message_id,
                conversation_id=conversation_id,
                parent_lead_id=parent_lead_id,
                lead_status='new',
                sender_email=email_data.get('sender_email'),
                sender_name=email_data.get('sender_name'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                received_at=email_data.get('received_at') or datetime.utcnow(),
                processed_at=datetime.utcnow(),

                # Extracted data
                product_type=extracted_data.get('product_type'),
                specific_ingredients=extracted_data.get('specific_ingredients'),
                delivery_format=extracted_data.get('delivery_format'),
                certifications_requested=extracted_data.get('certifications_requested'),

                estimated_quantity=extracted_data.get('estimated_quantity'),
                timeline_urgency=extracted_data.get('timeline_urgency'),
                budget_indicator=extracted_data.get('budget_indicator'),
                experience_level=extracted_data.get('experience_level'),
                distribution_channel=extracted_data.get('distribution_channel'),
                has_existing_brand=extracted_data.get('has_existing_brand'),

                lead_quality_score=extracted_data.get('lead_quality_score'),
                response_priority=extracted_data.get('response_priority'),

                specific_questions=extracted_data.get('specific_questions'),
                geographic_region=extracted_data.get('geographic_region'),
                extraction_confidence=extracted_data.get('extraction_confidence'),
            )
            session.add(lead)
            await session.flush()

            lead_id = lead.id

            # Create email message record
            email_message = EmailMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                lead_id=lead_id,
                direction='inbound',
                message_type='email',
                email_headers=email_data.get('email_headers', {}),
                sender_email=email_data.get('sender_email'),
                sender_name=email_data.get('sender_name'),
                subject=email_data.get('subject'),
                body=email_data.get('body'),
                received_at=email_data.get('received_at') or datetime.utcnow()
            )
            session.add(email_message)

            await session.commit()

        logger.info(f"Saved follow-up lead {lead_id} (parent: {parent_lead_id})")

        # Generate response
        response_agent = get_response_agent()
        draft_data = await response_agent.generate_response(extracted_data)

        if draft_data:
            async with get_db_session() as session:
                draft = Draft(
                    lead_id=lead_id,
                    subject_line=draft_data.get('subject_line'),
                    draft_content=draft_data.get('draft_content'),
                    status=draft_data.get('status', 'pending'),
                    response_type=draft_data.get('response_type'),
                    confidence_score=draft_data.get('confidence_score'),
                    flags=draft_data.get('flags'),
                    rag_sources=draft_data.get('rag_sources'),
                )
                session.add(draft)

                # Update lead status
                result = await session.execute(
                    select(Lead).where(Lead.id == lead_id)
                )
                lead = result.scalar_one()
                lead.lead_status = 'responded'

                await session.commit()
                draft_id = draft.id
        else:
            draft_id = None

        logger.info(f"✅ Processed follow-up inquiry {message_id}")

        return {
            'status': 'success',
            'classification': 'follow_up_inquiry',
            'message_id': message_id,
            'lead_id': lead_id,
            'parent_lead_id': parent_lead_id,
            'conversation_id': conversation_id,
            'draft_id': draft_id,
            'days_since_last_contact': metadata.get('days_since_last_contact')
        }

    return asyncio.run(_process())


@celery_app.task(name='tasks.email_tasks.send_approved_draft')
def send_approved_draft(draft_id: int):
    """Send an approved draft via SMTP

    Args:
        draft_id: Draft ID to send
    """
    import asyncio

    async def _send():
        logger.info(f"Sending approved draft {draft_id}")

        try:
            email_service = get_email_service()

            # Get draft and lead from database
            async with get_db_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(Draft).where(Draft.id == draft_id)
                )
                draft = result.scalar_one_or_none()

                if not draft:
                    return {'status': 'error', 'reason': 'draft_not_found'}

                if draft.status != 'approved':
                    return {'status': 'error', 'reason': 'draft_not_approved'}

                # Get associated lead
                result = await session.execute(
                    select(Lead).where(Lead.id == draft.lead_id)
                )
                lead = result.scalar_one_or_none()

                if not lead:
                    return {'status': 'error', 'reason': 'lead_not_found'}

                # Send email
                success = await email_service.send_email(
                    to_email=lead.sender_email,
                    to_name=lead.sender_name,
                    subject=draft.subject_line,
                    body=draft.draft_content,
                    in_reply_to=lead.message_id
                )

                if success:
                    # Update draft status
                    draft.status = 'sent'
                    draft.sent_at = datetime.utcnow()

                    # Create outbound email message record
                    if lead.conversation_id:
                        # Generate a message ID for our sent email
                        import uuid
                        sent_message_id = f"<{uuid.uuid4()}@emailagent.local>"

                        email_message = EmailMessage(
                            message_id=sent_message_id,
                            conversation_id=lead.conversation_id,
                            lead_id=lead.id,
                            direction='outbound',
                            message_type='email',
                            email_headers={
                                'in_reply_to': lead.message_id,
                                'references': lead.message_id
                            },
                            sender_email=email_service.email_address,
                            sender_name='Sales Team',
                            recipient_email=lead.sender_email,
                            recipient_name=lead.sender_name,
                            subject=draft.subject_line,
                            body=draft.draft_content,
                            is_draft_sent=True,
                            draft_id=draft_id,
                            sent_at=datetime.utcnow()
                        )
                        session.add(email_message)

                        # Update conversation
                        result = await session.execute(
                            select(Conversation).where(Conversation.id == lead.conversation_id)
                        )
                        conversation = result.scalar_one_or_none()
                        if conversation:
                            conversation.last_message_id = sent_message_id
                            conversation.last_activity_at = datetime.utcnow()

                    # Capture edited drafts as training data for AI learning
                    if draft.edit_summary:
                        from models.database import HistoricalResponseExample
                        from rag.embeddings import get_embedding_generator

                        logger.info(f"📚 Capturing edited draft {draft_id} as training example")

                        try:
                            # Build inquiry text for embedding
                            inquiry_text = f"{lead.subject}\n\n{lead.body}" if lead.subject and lead.body else (lead.body or lead.subject or "")

                            # Generate embedding for semantic search
                            embedder = get_embedding_generator()
                            inquiry_embedding = await embedder.generate_query_embedding(inquiry_text)

                            # Create historical example with edited response
                            historical_example = HistoricalResponseExample(
                                inquiry_lead_id=lead.id,
                                inquiry_subject=lead.subject,
                                inquiry_body=lead.body,
                                inquiry_sender_email=lead.sender_email,
                                response_body=draft.draft_content,  # Edited version
                                response_subject=draft.subject_line,
                                response_date=datetime.utcnow(),
                                embedding=inquiry_embedding,
                                response_metadata={
                                    'was_edited': True,
                                    'edit_summary': draft.edit_summary,
                                    'original_confidence': draft.confidence_score,
                                    'source': 'edited_draft',
                                    'draft_id': draft_id
                                }
                            )
                            session.add(historical_example)
                            logger.info(f"✅ Saved edited draft as historical example for future learning")
                        except Exception as e:
                            logger.error(f"⚠️ Failed to capture edited draft as training data: {e}")
                            # Don't fail the whole send operation if training capture fails

                    await session.commit()

                    logger.info(f"✅ Sent draft {draft_id} to {lead.sender_email}")

                    return {
                        'status': 'success',
                        'draft_id': draft_id,
                        'recipient': lead.sender_email
                    }
                else:
                    return {'status': 'error', 'reason': 'smtp_send_failed'}

        except Exception as e:
            logger.error(f"Error sending draft {draft_id}: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    # Create a new event loop for this task to avoid loop conflicts
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_send())
    finally:
        loop.close()
