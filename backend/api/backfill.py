"""
API endpoints for historical email backfilling
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import get_db
from models.database import Lead, HistoricalResponseExample
from tasks.backfill_tasks import (
    backfill_historical_emails,
    analyze_response_patterns,
    test_historical_inbox_connection
)
from celery.result import AsyncResult
from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backfill", tags=["backfill"])


class BackfillStartRequest(BaseModel):
    """Request to start backfill"""
    limit: Optional[int] = None
    folder: str = "INBOX"


class BackfillStartResponse(BaseModel):
    """Response when starting backfill"""
    status: str
    task_id: str
    message: str


class BackfillStatusResponse(BaseModel):
    """Backfill task status response"""
    task_id: str
    state: str
    status: Optional[str] = None
    result: Optional[Dict] = None
    meta: Optional[Dict] = None


class BackfillSummaryResponse(BaseModel):
    """Summary of backfilled data"""
    historical_leads_count: int
    historical_responses_count: int
    total_leads_count: int
    sample_historical_leads: list


@router.post("/start", response_model=BackfillStartResponse)
async def start_backfill(request: BackfillStartRequest):
    """
    Start historical email backfill process

    This will fetch historical "Contact Form:" emails, match inquiry-response pairs,
    and store them in the database for AI learning.

    Args:
        request: Backfill configuration

    Returns:
        Task ID for tracking progress
    """
    try:
        logger.info(f"Starting backfill with limit={request.limit}, folder={request.folder}")

        # Start Celery task
        task = backfill_historical_emails.delay(
            limit=request.limit,
            folder=request.folder
        )

        return BackfillStartResponse(
            status="started",
            task_id=task.id,
            message=f"Backfill task started. Use /api/backfill/status/{task.id} to check progress."
        )

    except Exception as e:
        logger.error(f"Error starting backfill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=BackfillStatusResponse)
async def get_backfill_status(task_id: str):
    """
    Get status of backfill task

    Args:
        task_id: Celery task ID

    Returns:
        Task status and progress information
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = BackfillStatusResponse(
            task_id=task_id,
            state=task_result.state,
            status=None,
            result=None,
            meta=None
        )

        if task_result.state == 'PENDING':
            response.status = 'Task is pending or does not exist'

        elif task_result.state == 'PROCESSING':
            response.status = 'Task is processing'
            response.meta = task_result.info

        elif task_result.state == 'SUCCESS':
            response.status = 'Task completed successfully'
            response.result = task_result.result

        elif task_result.state == 'FAILURE':
            response.status = 'Task failed'
            response.result = {'error': str(task_result.info)}

        return response

    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=BackfillSummaryResponse)
async def get_backfill_summary(
    limit: int = Query(default=10, description="Number of sample leads to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of backfilled historical data

    Args:
        limit: Number of sample leads to return
        db: Database session

    Returns:
        Summary of historical leads and responses
    """
    try:
        # Count historical leads
        historical_leads_result = await db.execute(
            select(func.count(Lead.id)).where(Lead.is_historical == True)
        )
        historical_leads_count = historical_leads_result.scalar_one()

        # Count all leads
        total_leads_result = await db.execute(
            select(func.count(Lead.id))
        )
        total_leads_count = total_leads_result.scalar_one()

        # Count historical response examples
        historical_responses_result = await db.execute(
            select(func.count(HistoricalResponseExample.id)).where(
                HistoricalResponseExample.is_active == True
            )
        )
        historical_responses_count = historical_responses_result.scalar_one()

        # Get sample historical leads
        sample_leads_result = await db.execute(
            select(Lead)
            .where(Lead.is_historical == True)
            .order_by(Lead.received_at.desc())
            .limit(limit)
        )
        sample_leads = sample_leads_result.scalars().all()

        sample_leads_data = [
            {
                'id': lead.id,
                'sender_email': lead.sender_email,
                'sender_name': lead.sender_name,
                'subject': lead.subject,
                'received_at': lead.received_at.isoformat() if lead.received_at else None,
                'lead_quality_score': lead.lead_quality_score,
                'response_priority': lead.response_priority,
                'product_type': lead.product_type,
                'has_human_response': bool(lead.human_response_body)
            }
            for lead in sample_leads
        ]

        return BackfillSummaryResponse(
            historical_leads_count=historical_leads_count,
            historical_responses_count=historical_responses_count,
            total_leads_count=total_leads_count,
            sample_historical_leads=sample_leads_data
        )

    except Exception as e:
        logger.error(f"Error getting backfill summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-patterns")
async def trigger_pattern_analysis():
    """
    Trigger analysis of historical response patterns

    This will analyze all historical responses to extract writing style patterns.

    Returns:
        Task ID for tracking progress
    """
    try:
        logger.info("Starting pattern analysis task")

        # Start Celery task
        task = analyze_response_patterns.delay()

        return {
            'status': 'started',
            'task_id': task.id,
            'message': f"Pattern analysis started. Use /api/backfill/status/{task.id} to check progress."
        }

    except Exception as e:
        logger.error(f"Error starting pattern analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_connection():
    """
    Test connection to historical inbox

    Returns:
        Connection test results
    """
    try:
        logger.info("Testing historical inbox connection")

        # Start Celery task
        task = test_historical_inbox_connection.delay()

        # Wait for result (short task)
        result = task.get(timeout=30)

        return result

    except Exception as e:
        logger.error(f"Error testing connection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical-responses")
async def list_historical_responses(
    skip: int = Query(default=0, description="Number of records to skip"),
    limit: int = Query(default=20, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    List historical response examples

    Args:
        skip: Number of records to skip (pagination)
        limit: Number of records to return
        db: Database session

    Returns:
        List of historical response examples
    """
    try:
        # Query historical responses
        result = await db.execute(
            select(HistoricalResponseExample)
            .where(HistoricalResponseExample.is_active == True)
            .order_by(HistoricalResponseExample.response_date.desc())
            .offset(skip)
            .limit(limit)
        )
        responses = result.scalars().all()

        # Count total
        count_result = await db.execute(
            select(func.count(HistoricalResponseExample.id)).where(
                HistoricalResponseExample.is_active == True
            )
        )
        total_count = count_result.scalar_one()

        return {
            'total': total_count,
            'skip': skip,
            'limit': limit,
            'responses': [
                {
                    'id': r.id,
                    'inquiry_lead_id': r.inquiry_lead_id,
                    'inquiry_subject': r.inquiry_subject,
                    'inquiry_sender_email': r.inquiry_sender_email,
                    'response_subject': r.response_subject,
                    'response_date': r.response_date.isoformat() if r.response_date else None,
                    'response_word_count': r.response_metadata.get('word_count') if r.response_metadata else None,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                }
                for r in responses
            ]
        }

    except Exception as e:
        logger.error(f"Error listing historical responses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
