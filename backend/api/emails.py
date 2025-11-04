"""
Email checking API endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from tasks.email_tasks import check_new_emails

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/emails", tags=["emails"])


class CheckEmailsResponse(BaseModel):
    """Response when triggering email check"""
    status: str
    task_id: str
    message: str


@router.post("/check", response_model=CheckEmailsResponse)
async def trigger_email_check():
    """
    Manually trigger email check (fire-and-forget)

    Queues a Celery task to check for new emails. Does not wait for completion.
    The task runs in the background and new drafts will appear via polling.

    Returns:
        Task ID for reference (optional tracking)
    """
    try:
        # Queue the task (non-blocking)
        task = check_new_emails.delay()

        logger.info(f"Email check task queued: {task.id}")

        return CheckEmailsResponse(
            status="queued",
            task_id=task.id,
            message="Email check initiated. New emails will appear automatically."
        )

    except Exception as e:
        logger.error(f"Error queuing email check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
