"""
Background task processing with Celery
"""
import logging
from typing import Any, Dict, Optional
from celery import Celery
from celery.result import AsyncResult

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "fastapi_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="default",
    task_routes={
        "app.worker.tasks.send_email": {"queue": "email"},
        "app.worker.tasks.process_data": {"queue": "data_processing"},
        "app.worker.tasks.generate_report": {"queue": "reports"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)


class BackgroundTaskManager:
    """Manager for background tasks using Celery."""
    
    def __init__(self):
        self.celery_app = celery_app
    
    def submit_task(
        self,
        task_name: str,
        *args,
        queue: Optional[str] = None,
        countdown: Optional[int] = None,
        eta: Optional[Any] = None,
        expires: Optional[Any] = None,
        **kwargs
    ) -> str:
        """Submit a task to Celery."""
        try:
            task = self.celery_app.send_task(
                task_name,
                args=args,
                kwargs=kwargs,
                queue=queue,
                countdown=countdown,
                eta=eta,
                expires=expires,
            )
            
            logger.info(f"Task {task_name} submitted with ID: {task.id}")
            return task.id
        
        except Exception as e:
            logger.error(f"Failed to submit task {task_name}: {str(e)}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a task."""
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
                "info": result.info,
            }
        
        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "status": "ERROR",
                "error": str(e)
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Task {task_id} cancelled")
            return True
        
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """Get all active tasks."""
        try:
            inspect = self.celery_app.control.inspect()
            active_tasks = inspect.active()
            return active_tasks or {}
        
        except Exception as e:
            logger.error(f"Failed to get active tasks: {str(e)}")
            return {}
    
    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """Get all scheduled tasks."""
        try:
            inspect = self.celery_app.control.inspect()
            scheduled_tasks = inspect.scheduled()
            return scheduled_tasks or {}
        
        except Exception as e:
            logger.error(f"Failed to get scheduled tasks: {str(e)}")
            return {}
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        try:
            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()
            return stats or {}
        
        except Exception as e:
            logger.error(f"Failed to get worker stats: {str(e)}")
            return {}
    
    def purge_queue(self, queue_name: str) -> int:
        """Purge a queue."""
        try:
            result = self.celery_app.control.purge()
            logger.info(f"Queue {queue_name} purged")
            return result
        
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {str(e)}")
            return 0


# Global task manager instance
background_task_manager = BackgroundTaskManager()


# Convenience functions
def submit_email_task(
    to_email: str,
    subject: str,
    body: str,
    **kwargs
) -> str:
    """Submit an email task."""
    return background_task_manager.submit_task(
        "app.worker.tasks.send_email",
        to_email,
        subject,
        body,
        queue="email",
        **kwargs
    )


def submit_data_processing_task(
    data: Dict[str, Any],
    processing_type: str,
    **kwargs
) -> str:
    """Submit a data processing task."""
    return background_task_manager.submit_task(
        "app.worker.tasks.process_data",
        data,
        processing_type,
        queue="data_processing",
        **kwargs
    )


def submit_report_generation_task(
    report_type: str,
    parameters: Dict[str, Any],
    **kwargs
) -> str:
    """Submit a report generation task."""
    return background_task_manager.submit_task(
        "app.worker.tasks.generate_report",
        report_type,
        parameters,
        queue="reports",
        **kwargs
    )


def submit_user_notification_task(
    user_id: str,
    notification_type: str,
    data: Dict[str, Any],
    **kwargs
) -> str:
    """Submit a user notification task."""
    return background_task_manager.submit_task(
        "app.worker.tasks.send_user_notification",
        user_id,
        notification_type,
        data,
        queue="notifications",
        **kwargs
    )


def submit_batch_processing_task(
    items: list,
    batch_size: int = 100,
    **kwargs
) -> str:
    """Submit a batch processing task."""
    return background_task_manager.submit_task(
        "app.worker.tasks.process_batch",
        items,
        batch_size,
        queue="batch_processing",
        **kwargs
    )


def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get task status."""
    return background_task_manager.get_task_status(task_id)


def cancel_task(task_id: str) -> bool:
    """Cancel a task."""
    return background_task_manager.cancel_task(task_id)
