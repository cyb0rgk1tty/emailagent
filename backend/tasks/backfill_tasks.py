"""
Celery tasks for historical email backfilling
"""
import logging
import asyncio
from typing import Dict, Optional

from tasks.celery_app import celery_app
from services.historical_backfill import get_historical_backfill_service
from services.response_learning import get_response_style_analyzer

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.backfill_tasks.backfill_historical_emails', bind=True)
def backfill_historical_emails(
    self,
    limit: Optional[int] = None,
    folder: str = 'INBOX'
):
    """
    Celery task: Backfill historical emails and responses

    Args:
        limit: Optional limit on number of emails to process
        folder: IMAP folder to search

    Returns:
        Summary dictionary
    """
    import asyncio

    async def _backfill():
        logger.info(f"Starting backfill task (limit={limit}, folder={folder})")

        try:
            # Update task state to processing
            self.update_state(state='PROCESSING', meta={'status': 'Connecting to inbox...'})

            # Get backfill service
            backfill_service = get_historical_backfill_service()

            # Update state
            self.update_state(state='PROCESSING', meta={'status': 'Fetching emails...'})

            # Run backfill
            result = await backfill_service.backfill_historical_emails(
                limit=limit,
                folder=folder
            )

            if result.get('status') == 'success':
                # Analyze response patterns after backfill
                self.update_state(state='PROCESSING', meta={'status': 'Analyzing response patterns...'})

                try:
                    analyzer = get_response_style_analyzer()
                    patterns = await analyzer.analyze_all_responses()
                    result['patterns_analyzed'] = True
                    result['pattern_count'] = patterns.get('sample_count', 0)
                except Exception as e:
                    logger.error(f"Error analyzing patterns: {e}", exc_info=True)
                    result['patterns_analyzed'] = False

            logger.info(f"Backfill task completed: {result}")

            return result

        except Exception as e:
            logger.error(f"Error in backfill task: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    return asyncio.run(_backfill())


@celery_app.task(name='tasks.backfill_tasks.analyze_response_patterns')
def analyze_response_patterns():
    """
    Celery task: Analyze historical response patterns

    Returns:
        Analysis results dictionary
    """
    import asyncio

    async def _analyze():
        logger.info("Starting response pattern analysis")

        try:
            analyzer = get_response_style_analyzer()
            patterns = await analyzer.analyze_all_responses()

            logger.info(f"Analysis complete: {patterns.get('sample_count', 0)} responses analyzed")

            return {
                'status': 'success',
                'patterns': patterns
            }

        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    return asyncio.run(_analyze())


@celery_app.task(name='tasks.backfill_tasks.test_historical_inbox_connection')
def test_historical_inbox_connection():
    """
    Celery task: Test connection to historical inbox

    Returns:
        Connection test results
    """
    import asyncio

    async def _test():
        logger.info("Testing historical inbox connection")

        try:
            backfill_service = get_historical_backfill_service()

            # Try to fetch just 1 email as a connection test
            emails = await backfill_service.fetch_contact_form_emails(limit=1)

            if emails is not None:
                return {
                    'status': 'success',
                    'message': f'Successfully connected. Found {len(emails)} test email(s).'
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to connect to historical inbox'
                }

        except Exception as e:
            logger.error(f"Error testing connection: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    return asyncio.run(_test())
