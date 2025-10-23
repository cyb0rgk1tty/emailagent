#!/usr/bin/env python3
"""
Regenerate drafts for leads that don't have associated drafts
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db_session
from models.database import Lead, Draft
from agents.response_agent import get_response_agent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_leads_without_drafts():
    """Find all leads that don't have associated drafts

    Returns:
        List of lead IDs without drafts
    """
    async with get_db_session() as session:
        # Get all lead IDs
        result = await session.execute(select(Lead.id))
        all_lead_ids = set(r[0] for r in result.fetchall())

        # Get all lead IDs that have drafts
        result = await session.execute(select(Draft.lead_id).distinct())
        leads_with_drafts = set(r[0] for r in result.fetchall())

        # Find leads without drafts
        leads_without_drafts = all_lead_ids - leads_with_drafts

        return sorted(list(leads_without_drafts))


async def regenerate_draft_for_lead(lead_id: int):
    """Regenerate draft for a specific lead

    Args:
        lead_id: ID of the lead

    Returns:
        True if successful, False otherwise
    """
    try:
        async with get_db_session() as session:
            # Fetch lead data
            result = await session.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead:
                logger.error(f"Lead {lead_id} not found")
                return False

            logger.info(f"Generating draft for lead {lead_id}: {lead.sender_email}")

            # Build lead data dictionary
            lead_data = {
                'sender_email': lead.sender_email,
                'sender_name': lead.sender_name,
                'subject': lead.subject,
                'body': lead.body,
                'product_type': lead.product_type or [],
                'certifications_requested': lead.certifications_requested or [],
                'delivery_format': lead.delivery_format or [],
                'estimated_quantity': lead.estimated_quantity,
                'timeline_urgency': lead.timeline_urgency,
                'experience_level': lead.experience_level,
                'specific_questions': lead.specific_questions or [],
                'lead_quality_score': lead.lead_quality_score,
                'response_priority': lead.response_priority,
            }

            # Generate response
            response_agent = get_response_agent()
            draft_data = await response_agent.generate_response(lead_data)

            if not draft_data:
                logger.error(f"Failed to generate draft for lead {lead_id}")
                return False

            logger.info(
                f"Generated draft (confidence: {draft_data.get('confidence_score')}, "
                f"type: {draft_data.get('response_type')})"
            )

            # Save draft
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

            logger.info(f"✅ Successfully created draft for lead {lead_id}")
            return True

    except Exception as e:
        logger.error(f"Error generating draft for lead {lead_id}: {e}", exc_info=True)
        return False


async def main():
    """Main function to regenerate all missing drafts"""
    logger.info("=" * 80)
    logger.info("Regenerating Missing Drafts")
    logger.info("=" * 80)

    # Find leads without drafts
    leads_without_drafts = await find_leads_without_drafts()

    if not leads_without_drafts:
        logger.info("✅ All leads already have drafts!")
        return

    logger.info(f"Found {len(leads_without_drafts)} leads without drafts: {leads_without_drafts}")

    # Regenerate drafts
    success_count = 0
    for lead_id in leads_without_drafts:
        logger.info(f"\n{'─' * 80}")
        if await regenerate_draft_for_lead(lead_id):
            success_count += 1
        logger.info(f"{'─' * 80}\n")

    # Summary
    logger.info("=" * 80)
    logger.info(f"Summary: Generated {success_count}/{len(leads_without_drafts)} drafts")
    logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
