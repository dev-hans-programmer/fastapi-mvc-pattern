"""
Celery application configuration.
"""
from celery import Celery
from kombu import Queue

from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "fastapi_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.user_tasks",
        "app.tasks.product_tasks",
        "app.tasks.order_tasks",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    task_routes={
        "app.tasks.user_tasks.*": {"queue": "user_queue"},
        "app.tasks.product_tasks.*": {"queue": "product_queue"},
        "app.tasks.order_tasks.*": {"queue": "order_queue"},
    },
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("user_queue", routing_key="user"),
        Queue("product_queue", routing_key="product"),
        Queue("order_queue", routing_key="order"),
        Queue("high_priority", routing_key="high"),
        Queue("low_priority", routing_key="low"),
    ),
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "app.tasks.user_tasks.cleanup_expired_tokens",
        "schedule": 3600.0,  # Every hour
    },
    "update-product-stats": {
        "task": "app.tasks.product_tasks.update_product_statistics",
        "schedule": 1800.0,  # Every 30 minutes
    },
    "process-pending-orders": {
        "task": "app.tasks.order_tasks.process_pending_orders",
        "schedule": 300.0,  # Every 5 minutes
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f"Request: {self.request!r}")
    return "Debug task completed"
