"""
Analytics API endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional
from datetime import datetime, timedelta

from database import get_db
from models.database import Lead, Draft, ProductTypeTrend
from models.schemas import AnalyticsOverview, ProductTypeTrendResponse

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    """Get summary analytics for dashboard"""
    # Total leads (all time)
    total_leads_result = await db.execute(select(func.count(Lead.id)))
    total_leads = total_leads_result.scalar() or 0

    # Spam leads count
    spam_leads_result = await db.execute(
        select(func.count(Lead.id)).where(Lead.lead_status == 'spam')
    )
    spam_leads = spam_leads_result.scalar() or 0

    # Legitimate leads count
    legitimate_leads = total_leads - spam_leads

    # Average response time (placeholder - would need actual sent timestamps)
    avg_response_time = "<1m"

    # Spam rate percentage
    spam_rate = (spam_leads / total_leads * 100) if total_leads > 0 else 0.0

    return {
        "total_leads": total_leads,
        "legitimate_leads": legitimate_leads,
        "spam_leads": spam_leads,
        "spam_rate": round(spam_rate, 1),
        "avg_response_time": avg_response_time
    }


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(7, ge=1, le=3650),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics overview"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Total leads (excluding spam)
    total_leads_result = await db.execute(
        select(func.count(Lead.id))
        .where(Lead.received_at >= cutoff_date)
        .where(Lead.lead_status != 'spam')
    )
    total_leads = total_leads_result.scalar() or 0

    # Spam leads count
    spam_leads_result = await db.execute(
        select(func.count(Lead.id))
        .where(Lead.received_at >= cutoff_date)
        .where(Lead.lead_status == 'spam')
    )
    spam_leads = spam_leads_result.scalar() or 0

    # Total drafts
    total_drafts_result = await db.execute(select(func.count(Draft.id)))
    total_drafts = total_drafts_result.scalar() or 0

    # Pending drafts
    pending_drafts_result = await db.execute(
        select(func.count(Draft.id)).where(Draft.status == 'pending')
    )
    pending_drafts = pending_drafts_result.scalar() or 0

    # Average quality score (excluding spam)
    avg_score_result = await db.execute(
        select(func.avg(Lead.lead_quality_score))
        .where(Lead.received_at >= cutoff_date)
        .where(Lead.lead_status != 'spam')
        .where(Lead.lead_quality_score.isnot(None))
    )
    avg_quality_score = avg_score_result.scalar() or 0.0

    # Approval rate
    approved_result = await db.execute(
        select(func.count(Draft.id)).where(Draft.status.in_(['approved', 'sent']))
    )
    approved = approved_result.scalar() or 0
    approval_rate = (approved / total_drafts * 100) if total_drafts > 0 else 0.0

    # Leads by priority (excluding spam)
    priority_result = await db.execute(
        select(Lead.response_priority, func.count(Lead.id))
        .where(Lead.received_at >= cutoff_date)
        .where(Lead.lead_status != 'spam')
        .where(Lead.response_priority.isnot(None))
        .group_by(Lead.response_priority)
    )
    leads_by_priority = {row[0]: row[1] for row in priority_result.all()}

    # Leads by product type (using unnest to expand arrays)
    # PostgreSQL-specific query to count each product type from array columns
    product_query = text("""
        SELECT pt as product_type, COUNT(*) as count
        FROM leads l, unnest(l.product_type) as pt
        WHERE l.received_at >= :cutoff_date
        AND l.lead_status != 'spam'
        AND pt IS NOT NULL
        GROUP BY pt
        ORDER BY count DESC
        LIMIT 10
    """)
    product_result = await db.execute(product_query, {"cutoff_date": cutoff_date})
    leads_by_product_type = {row[0]: row[1] for row in product_result.all()}

    # Recent activity (last 10 items, excluding spam)
    recent_leads = await db.execute(
        select(Lead)
        .where(Lead.received_at >= cutoff_date)
        .where(Lead.lead_status != 'spam')
        .order_by(Lead.received_at.desc())
        .limit(10)
    )
    recent_activity = [
        {
            "type": "lead",
            "id": lead.id,
            "email": lead.sender_email,
            "score": lead.lead_quality_score,
            "timestamp": lead.received_at.isoformat()
        }
        for lead in recent_leads.scalars().all()
    ]

    return {
        "total_leads": total_leads,
        "spam_leads": spam_leads,
        "total_drafts": total_drafts,
        "pending_drafts": pending_drafts,
        "avg_quality_score": round(float(avg_quality_score), 2),
        "approval_rate": round(approval_rate, 2),
        "leads_by_priority": leads_by_priority,
        "leads_by_product_type": leads_by_product_type,
        "recent_activity": recent_activity
    }


@router.get("/product-trends")
async def get_product_trends(
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_db)
):
    """Get product type trends"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(ProductTypeTrend)
        .where(ProductTypeTrend.date >= cutoff_date)
        .order_by(ProductTypeTrend.date.desc())
    )
    trends = result.scalars().all()

    return {"trends": [ProductTypeTrendResponse.model_validate(t) for t in trends]}


@router.get("/product-types")
async def get_product_type_distribution(
    days: int = Query(7, ge=1, le=3650),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get product type distribution (top N product types by count)

    Uses PostgreSQL unnest to properly handle array columns.
    Excludes spam leads.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # PostgreSQL query to expand arrays and count occurrences
    query = text("""
        SELECT pt as product_type, COUNT(*) as count
        FROM leads l, unnest(l.product_type) as pt
        WHERE l.received_at >= :cutoff_date
        AND l.lead_status != 'spam'
        AND pt IS NOT NULL
        GROUP BY pt
        ORDER BY count DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {"cutoff_date": cutoff_date, "limit": limit})

    product_types = [
        {"name": row[0], "value": row[1]}
        for row in result.all()
    ]

    return {"product_types": product_types}


@router.get("/export/{format}")
async def export_analytics(
    format: str,
    days: int = Query(30, ge=1, le=3650),
    db: AsyncSession = Depends(get_db)
):
    """Export analytics data (CSV or PDF)"""
    # Placeholder - will implement actual export in Phase 5
    return {
        "message": f"Export to {format} will be implemented in Phase 5",
        "days": days
    }
