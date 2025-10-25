"""
Script to reprocess email body formatting for existing leads in the database.
This applies the new HTML-to-text conversion to emails that were processed
with the old crude regex method.
"""
import asyncio
import logging
from sqlalchemy import select, update
from database import get_db_session
from models.database import Lead
from utils.email_utils import html_to_text, add_line_breaks_to_plain_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reprocess_lead_formatting(lead_id: int = None):
    """
    Reprocess email body formatting for leads.

    Args:
        lead_id: Specific lead ID to reprocess, or None to process all
    """
    async with get_db_session() as db:
        # Build query
        if lead_id:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            leads = result.scalars().all()
        else:
            result = await db.execute(
                select(Lead).order_by(Lead.id)
            )
            leads = result.scalars().all()

        logger.info(f"Found {len(leads)} leads to process")

        updated_count = 0
        for lead in leads:
            if not lead.body:
                continue

            original_body = lead.body

            # First, try HTML-to-text conversion (works if HTML tags still present)
            cleaned_body = html_to_text(original_body)

            # If no newlines were added, it means the text was already stripped
            # Apply intelligent line break insertion
            if '\n' not in cleaned_body or cleaned_body.count('\n') < 3:
                cleaned_body = add_line_breaks_to_plain_text(cleaned_body)

            # Check if anything changed
            if cleaned_body != original_body:
                lead.body = cleaned_body
                updated_count += 1
                logger.info(f"Updated lead {lead.id} - {lead.sender_name}")
                logger.debug(f"  Old length: {len(original_body)}, New length: {len(cleaned_body)}")
                logger.debug(f"  Old newlines: {original_body.count(chr(10))}, New newlines: {cleaned_body.count(chr(10))}")

        if updated_count > 0:
            await db.commit()
            logger.info(f"✅ Successfully updated {updated_count} leads")
        else:
            logger.info("No leads needed updating")


if __name__ == "__main__":
    import sys

    lead_id = None
    if len(sys.argv) > 1:
        lead_id = int(sys.argv[1])
        print(f"Reprocessing lead ID: {lead_id}")
    else:
        print("Reprocessing all leads...")

    asyncio.run(reprocess_lead_formatting(lead_id))
