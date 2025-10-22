"""
Celery application configuration
Background task processing for email ingestion and agent pipeline
"""
from celery import Celery
from celery.schedules import crontab
from config import settings

# Create Celery app
celery_app = Celery(
    "supplement_leads",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['tasks.email_tasks', 'tasks.analytics_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    # Check for new emails every 5 minutes
    'check-new-emails': {
        'task': 'tasks.email_tasks.check_new_emails',
        'schedule': 300.0,  # 5 minutes in seconds
    },

    # Generate daily analytics snapshot at midnight
    'daily-analytics-snapshot': {
        'task': 'tasks.analytics_tasks.generate_daily_snapshot',
        'schedule': crontab(hour=0, minute=0),  # Midnight UTC
    },

    # Update trending products every hour
    'hourly-trending-update': {
        'task': 'tasks.analytics_tasks.update_trending_products',
        'schedule': crontab(minute=0),  # Every hour
    },
}

if __name__ == '__main__':
    celery_app.start()
