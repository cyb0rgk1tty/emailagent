"""
Analytics Agent - Generates insights and trends from lead data
Tracks product trends, lead quality, and business intelligence
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from models.database import Lead, Draft, ProductTypeTrend, AnalyticsSnapshot
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsAgent:
    """Agent for generating analytics and insights"""

    def __init__(self):
        """Initialize analytics agent"""
        logger.info("Initialized Analytics Agent")

    async def track_product_trend(
        self,
        product_type: str,
        date: datetime = None
    ) -> None:
        """Track a product type mention

        Args:
            product_type: Product type mentioned
            date: Date of mention (default: now)
        """
        if not date:
            date = datetime.utcnow()

        try:
            async with get_db_session() as session:
                # Check if trend exists for today
                result = await session.execute(
                    select(ProductTypeTrend).where(
                        and_(
                            ProductTypeTrend.product_type == product_type,
                            func.date(ProductTypeTrend.date) == date.date()
                        )
                    )
                )

                trend = result.scalar_one_or_none()

                if trend:
                    # Increment existing trend
                    trend.mention_count += 1
                else:
                    # Create new trend
                    trend = ProductTypeTrend(
                        product_type=product_type,
                        date=date,
                        mention_count=1,
                        lead_count=1
                    )
                    session.add(trend)

                await session.commit()

                logger.debug(f"Tracked trend: {product_type}")

        except Exception as e:
            logger.error(f"Error tracking product trend: {e}")

    async def update_product_trends_from_lead(self, lead_id: int) -> None:
        """Update product trends from a lead's data

        Args:
            lead_id: Lead ID
        """
        try:
            async with get_db_session() as session:
                # Get lead
                result = await session.execute(
                    select(Lead).where(Lead.id == lead_id)
                )
                lead = result.scalar_one_or_none()

                if not lead:
                    return

                # Track each product type mentioned
                product_types = lead.product_type or []

                for product in product_types:
                    await self.track_product_trend(
                        product_type=product,
                        date=lead.received_at or datetime.utcnow()
                    )

                logger.info(f"Updated trends for lead {lead_id}: {len(product_types)} products")

        except Exception as e:
            logger.error(f"Error updating trends from lead: {e}")

    async def generate_daily_snapshot(self, date: datetime = None) -> Optional[Dict]:
        """Generate daily analytics snapshot

        Args:
            date: Date to generate snapshot for (default: today)

        Returns:
            Snapshot data dictionary
        """
        if not date:
            date = datetime.utcnow()

        try:
            async with get_db_session() as session:
                # Get date range for "today"
                start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
                end_date = start_date + timedelta(days=1)

                # Count leads received today
                result = await session.execute(
                    select(func.count(Lead.id)).where(
                        and_(
                            Lead.received_at >= start_date,
                            Lead.received_at < end_date
                        )
                    )
                )
                leads_today = result.scalar() or 0

                # Count drafts created today
                result = await session.execute(
                    select(func.count(Draft.id)).where(
                        and_(
                            Draft.created_at >= start_date,
                            Draft.created_at < end_date
                        )
                    )
                )
                drafts_today = result.scalar() or 0

                # Average lead quality score today
                result = await session.execute(
                    select(func.avg(Lead.lead_quality_score)).where(
                        and_(
                            Lead.received_at >= start_date,
                            Lead.received_at < end_date,
                            Lead.lead_quality_score.isnot(None)
                        )
                    )
                )
                avg_quality = result.scalar() or 0.0

                # Priority breakdown
                result = await session.execute(
                    select(
                        Lead.response_priority,
                        func.count(Lead.id)
                    ).where(
                        and_(
                            Lead.received_at >= start_date,
                            Lead.received_at < end_date
                        )
                    ).group_by(Lead.response_priority)
                )
                priority_breakdown = {row[0]: row[1] for row in result.all()}

                # Top product types today
                result = await session.execute(
                    select(
                        ProductTypeTrend.product_type,
                        func.sum(ProductTypeTrend.mention_count)
                    ).where(
                        func.date(ProductTypeTrend.date) == date.date()
                    ).group_by(ProductTypeTrend.product_type)
                    .order_by(func.sum(ProductTypeTrend.mention_count).desc())
                    .limit(10)
                )
                top_products = [
                    {'product': row[0], 'mentions': row[1]}
                    for row in result.all()
                ]

                snapshot_data = {
                    'date': date.isoformat(),
                    'leads_received': leads_today,
                    'drafts_created': drafts_today,
                    'avg_lead_quality': float(avg_quality),
                    'priority_breakdown': priority_breakdown,
                    'top_products': top_products,
                    'conversion_rate': (drafts_today / leads_today * 100) if leads_today > 0 else 0
                }

                # Store snapshot
                snapshot = AnalyticsSnapshot(
                    snapshot_date=date,
                    period_type='daily',
                    metrics=snapshot_data
                )

                session.add(snapshot)
                await session.commit()

                logger.info(f"Generated daily snapshot for {date.date()}")
                return snapshot_data

        except Exception as e:
            logger.error(f"Error generating daily snapshot: {e}")
            return None

    async def get_trending_products(self, days: int = 7) -> List[Dict]:
        """Get trending product types

        Args:
            days: Number of days to analyze

        Returns:
            List of trending products with growth metrics
        """
        try:
            async with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Get product mentions in the time period
                result = await session.execute(
                    select(
                        ProductTypeTrend.product_type,
                        func.sum(ProductTypeTrend.mention_count).label('total_mentions'),
                        func.count(ProductTypeTrend.lead_count).label('lead_count')
                    ).where(
                        ProductTypeTrend.date >= cutoff_date
                    ).group_by(ProductTypeTrend.product_type)
                    .order_by(func.sum(ProductTypeTrend.mention_count).desc())
                )

                products = [
                    {
                        'product_type': row[0],
                        'mentions': row[1],
                        'leads': row[2]
                    }
                    for row in result.all()
                ]

                logger.info(f"Retrieved {len(products)} trending products")
                return products

        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return []

    async def get_lead_stats(self, days: int = 30) -> Dict:
        """Get lead statistics

        Args:
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        try:
            async with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Total leads
                result = await session.execute(
                    select(func.count(Lead.id)).where(
                        Lead.received_at >= cutoff_date
                    )
                )
                total_leads = result.scalar() or 0

                # Average quality score
                result = await session.execute(
                    select(func.avg(Lead.lead_quality_score)).where(
                        and_(
                            Lead.received_at >= cutoff_date,
                            Lead.lead_quality_score.isnot(None)
                        )
                    )
                )
                avg_quality = result.scalar() or 0.0

                # Priority distribution
                result = await session.execute(
                    select(
                        Lead.response_priority,
                        func.count(Lead.id)
                    ).where(
                        Lead.received_at >= cutoff_date
                    ).group_by(Lead.response_priority)
                )
                priority_dist = {row[0]: row[1] for row in result.all()}

                # Top certifications requested
                # This is tricky with ARRAY fields, we'll do it in Python
                result = await session.execute(
                    select(Lead.certifications_requested).where(
                        and_(
                            Lead.received_at >= cutoff_date,
                            Lead.certifications_requested.isnot(None)
                        )
                    )
                )

                all_certs = []
                for row in result.all():
                    certs = row[0] or []
                    all_certs.extend(certs)

                cert_counts = Counter(all_certs)
                top_certifications = [
                    {'certification': cert, 'count': count}
                    for cert, count in cert_counts.most_common(10)
                ]

                return {
                    'total_leads': total_leads,
                    'avg_quality_score': float(avg_quality),
                    'priority_distribution': priority_dist,
                    'top_certifications': top_certifications,
                    'period_days': days
                }

        except Exception as e:
            logger.error(f"Error getting lead stats: {e}")
            return {}

    async def get_response_metrics(self, days: int = 30) -> Dict:
        """Get draft response metrics

        Args:
            days: Number of days to analyze

        Returns:
            Metrics dictionary
        """
        try:
            async with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                # Total drafts
                result = await session.execute(
                    select(func.count(Draft.id)).where(
                        Draft.created_at >= cutoff_date
                    )
                )
                total_drafts = result.scalar() or 0

                # Status distribution
                result = await session.execute(
                    select(
                        Draft.status,
                        func.count(Draft.id)
                    ).where(
                        Draft.created_at >= cutoff_date
                    ).group_by(Draft.status)
                )
                status_dist = {row[0]: row[1] for row in result.all()}

                # Average confidence score
                result = await session.execute(
                    select(func.avg(Draft.confidence_score)).where(
                        and_(
                            Draft.created_at >= cutoff_date,
                            Draft.confidence_score.isnot(None)
                        )
                    )
                )
                avg_confidence = result.scalar() or 0.0

                # Approval rate
                approved = status_dist.get('approved', 0) + status_dist.get('sent', 0)
                approval_rate = (approved / total_drafts * 100) if total_drafts > 0 else 0

                return {
                    'total_drafts': total_drafts,
                    'status_distribution': status_dist,
                    'avg_confidence_score': float(avg_confidence),
                    'approval_rate': approval_rate,
                    'period_days': days
                }

        except Exception as e:
            logger.error(f"Error getting response metrics: {e}")
            return {}


# Singleton instance
_agent = None

def get_analytics_agent() -> AnalyticsAgent:
    """Get singleton analytics agent instance"""
    global _agent
    if _agent is None:
        _agent = AnalyticsAgent()
    return _agent
