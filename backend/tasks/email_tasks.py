"""
Celery tasks for email processing
Handles email ingestion, extraction, and response generation
"""
import logging
from typing import Dict, List
from datetime import datetime

from tasks.celery_app import celery_app
from database import get_db_session
from models.database import Lead, Draft
from agents import get_extraction_agent, get_response_agent, get_analytics_agent
from services.email_service import get_email_service

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.email_tasks.check_new_emails')
def check_new_emails():
    """Periodic task: Check for new emails and process them"""
    import asyncio

    async def _check():
        logger.info("Checking for new emails...")

        try:
            email_service = get_email_service()

            # Fetch new emails
            new_emails = await email_service.fetch_new_emails(limit=50)

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
        logger.info(f"Processing email: {message_id}")

        try:
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

            # Step 2: Save lead to database
            async with get_db_session() as session:
                lead = Lead(
                    message_id=message_id,
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

                await session.commit()

            logger.info(f"Saved lead {lead_id} to database")

            # Step 3: Generate response
            response_agent = get_response_agent()
            draft_data = await response_agent.generate_response(extracted_data)

            if not draft_data:
                logger.error(f"Failed to generate response for lead {lead_id}")
                return {'status': 'error', 'step': 'response_generation', 'lead_id': lead_id}

            logger.info(f"Generated draft (confidence: {draft_data.get('confidence_score')})")

            # Step 4: Save draft to database
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
                await session.commit()

                draft_id = draft.id

            logger.info(f"Saved draft {draft_id} to database")

            # Step 5: Update analytics
            analytics_agent = get_analytics_agent()
            await analytics_agent.update_product_trends_from_lead(lead_id)

            logger.info(f"✅ Successfully processed email {message_id}")

            return {
                'status': 'success',
                'message_id': message_id,
                'lead_id': lead_id,
                'draft_id': draft_id,
                'lead_quality_score': extracted_data.get('lead_quality_score'),
                'response_priority': extracted_data.get('response_priority'),
            }

        except Exception as e:
            logger.error(f"Error processing email {message_id}: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e), 'message_id': message_id}

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

    return asyncio.run(_send())
