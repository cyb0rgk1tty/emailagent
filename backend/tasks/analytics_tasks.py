"""
Celery tasks for analytics generation
Periodic tasks for generating insights and snapshots
"""
import logging
from datetime import datetime, timedelta

from tasks.celery_app import celery_app
from agents import get_analytics_agent

logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.analytics_tasks.generate_daily_snapshot')
def generate_daily_snapshot():
    """Generate daily analytics snapshot"""
    import asyncio

    async def _generate():
        logger.info("Generating daily analytics snapshot...")

        try:
            analytics_agent = get_analytics_agent()

            # Generate snapshot for yesterday (complete day)
            yesterday = datetime.utcnow() - timedelta(days=1)

            snapshot = await analytics_agent.generate_daily_snapshot(date=yesterday)

            if snapshot:
                logger.info(
                    f"✅ Generated daily snapshot: "
                    f"{snapshot.get('leads_received')} leads, "
                    f"{snapshot.get('drafts_created')} drafts, "
                    f"avg quality {snapshot.get('avg_lead_quality'):.1f}"
                )

                return {
                    'status': 'success',
                    'date': snapshot.get('date'),
                    'metrics': snapshot
                }
            else:
                return {'status': 'error', 'reason': 'snapshot_generation_failed'}

        except Exception as e:
            logger.error(f"Error generating daily snapshot: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    return asyncio.run(_generate())


@celery_app.task(name='tasks.analytics_tasks.update_trending_products')
def update_trending_products():
    """Update trending product types"""
    import asyncio

    async def _update():
        logger.info("Updating trending products...")

        try:
            analytics_agent = get_analytics_agent()

            # Get trending products for last 7 days
            trending = await analytics_agent.get_trending_products(days=7)

            logger.info(
                f"✅ Updated trending products: {len(trending)} products tracked"
            )

            return {
                'status': 'success',
                'product_count': len(trending),
                'top_products': trending[:5] if trending else []
            }

        except Exception as e:
            logger.error(f"Error updating trending products: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    return asyncio.run(_update())


@celery_app.task(name='tasks.analytics_tasks.generate_weekly_report')
def generate_weekly_report():
    """Generate weekly analytics report"""
    import asyncio

    async def _generate():
        logger.info("Generating weekly analytics report...")

        try:
            analytics_agent = get_analytics_agent()

            # Get stats for last 7 days
            lead_stats = await analytics_agent.get_lead_stats(days=7)
            response_metrics = await analytics_agent.get_response_metrics(days=7)
            trending = await analytics_agent.get_trending_products(days=7)

            report = {
                'period': 'weekly',
                'lead_stats': lead_stats,
                'response_metrics': response_metrics,
                'trending_products': trending[:10],
                'generated_at': datetime.utcnow().isoformat()
            }

            logger.info(
                f"✅ Generated weekly report: "
                f"{lead_stats.get('total_leads', 0)} leads, "
                f"{response_metrics.get('total_drafts', 0)} drafts"
            )

            return {
                'status': 'success',
                'report': report
            }

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}

    return asyncio.run(_generate())
