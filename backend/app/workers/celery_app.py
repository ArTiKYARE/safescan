"""
SafeScan — Celery Application
"""

import signal
import sys
from celery import Celery
from celery.signals import worker_shutdown, worker_init

from app.core.config import settings

celery_app = Celery(
    "safescan",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks",
    ],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.workers.tasks.run_scan": {"queue": "scans"},
        "app.workers.tasks.verify_domain": {"queue": "verification"},
    },

    # Rate limiting
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # Timeouts
    task_soft_time_limit=240,
    task_time_limit=300,

    # Retry
    task_acks_on_failure_or_timeout=False,

    # Result expiration
    result_expires=3600,

    # Resource limits
    worker_max_tasks_per_child=50,
    worker_max_memory_per_child=500000,

    # Connection pooling
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
)

# Task scheduling (periodic tasks)
celery_app.conf.beat_schedule = {
    "cleanup-old-data": {
        "task": "app.workers.tasks.cleanup_old_data",
        "schedule": 86400.0,  # Every 24 hours
    },
    "reverify-domains": {
        "task": "app.workers.tasks.reverify_domains",
        "schedule": 2592000.0,  # Every 30 days
    },
}


@worker_init.connect
def init_worker(**kwargs):
    """Initialize worker signal handlers for graceful shutdown."""
    def graceful_shutdown(signum, frame):
        sig_name = signal.Signals(signum).name
        print(f"\n⚠️  Received signal {sig_name}, initiating graceful shutdown...")
        celery_app.control.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, graceful_shutdown)
    signal.signal(signal.SIGINT, graceful_shutdown)


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Clean up resources on worker shutdown."""
    print("🧹 Celery worker shutting down gracefully...")
    from app.workers.scan_logger import _RedisPool
    _RedisPool.close()


def create_scan_task(scan_id: str, domain: str, modules: list[str]):
    """Helper to create a scan task."""
    from app.workers.tasks import run_scan
    return run_scan.delay(scan_id, domain, modules)
