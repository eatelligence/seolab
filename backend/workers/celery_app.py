from celery import Celery
from celery.schedules import crontab

from config import settings

celery = Celery(
    "seolab",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["workers.tasks"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery.conf.beat_schedule = {
    "rank-tracker-daily": {
        "task": "workers.tasks.run_rank_tracker_for_all_projects",
        "schedule": crontab(hour=6, minute=0),
    },
    "site-audit-weekly": {
        "task": "workers.tasks.run_site_audit_for_all_projects",
        "schedule": crontab(hour=4, minute=0, day_of_week=1),  # Monday 04:00 UTC
    },
    "backlink-snapshot-daily": {
        "task": "workers.tasks.snapshot_backlinks_for_all_projects",
        "schedule": crontab(hour=5, minute=0),
    },
    "ai-visibility-daily": {
        "task": "workers.tasks.run_ai_visibility_for_all_projects",
        "schedule": crontab(hour=7, minute=0),
    },
}
