"""
Background task processing with Celery
"""
import logging
from typing import Any, Dict, Optional
from celery import Celery, Task
from celery.result import AsyncResult
from celery.signals import task_prerun, task_postrun, task_failure

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "fastapi_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.core.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    broker_connection_retry_on_startup=True,
)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Success callback"""
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback"""
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Retry callback"""
        logger.warning(f"Task {task_id} retrying: {exc}")


# Task signal handlers
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Task prerun handler"""
    logger.info(f"Task {task_id} started: {task.name}")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Task postrun handler"""
    logger.info(f"Task {task_id} completed with state: {state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Task failure handler"""
    logger.error(f"Task {task_id} failed: {exception}")


# Task definitions
@celery_app.task(bind=True, base=CallbackTask)
def sample_task(self, name: str, delay: int = 10):
    """Sample background task"""
    import time
    
    try:
        logger.info(f"Starting sample task for {name}")
        
        # Simulate work
        for i in range(delay):
            time.sleep(1)
            self.update_state(
                state="PROGRESS",
                meta={"current": i + 1, "total": delay, "status": f"Processing {name}..."}
            )
        
        result = {"status": "completed", "name": name, "message": f"Task completed for {name}"}
        logger.info(f"Sample task completed for {name}")
        return result
        
    except Exception as exc:
        logger.error(f"Sample task failed for {name}: {exc}")
        raise


@celery_app.task(bind=True, base=CallbackTask)
def send_email_task(self, to_email: str, subject: str, body: str):
    """Send email task"""
    try:
        logger.info(f"Sending email to {to_email}")
        
        # Simulate email sending
        import time
        time.sleep(2)
        
        # In a real implementation, you would integrate with an email service
        # like SendGrid, AWS SES, or SMTP
        
        result = {
            "status": "sent",
            "to": to_email,
            "subject": subject,
            "timestamp": time.time()
        }
        
        logger.info(f"Email sent successfully to {to_email}")
        return result
        
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        raise


@celery_app.task(bind=True, base=CallbackTask)
def process_data_task(self, data: Dict[str, Any]):
    """Process data task"""
    try:
        logger.info(f"Processing data: {data}")
        
        # Simulate data processing
        import time
        time.sleep(5)
        
        result = {
            "status": "processed",
            "original_data": data,
            "processed_at": time.time(),
            "result": "Data processed successfully"
        }
        
        logger.info("Data processing completed")
        return result
        
    except Exception as exc:
        logger.error(f"Data processing failed: {exc}")
        raise


@celery_app.task(bind=True, base=CallbackTask)
def cleanup_task(self):
    """Cleanup task"""
    try:
        logger.info("Starting cleanup task")
        
        # Simulate cleanup operations
        import time
        time.sleep(3)
        
        result = {
            "status": "completed",
            "cleaned_items": 100,
            "timestamp": time.time()
        }
        
        logger.info("Cleanup task completed")
        return result
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
        raise


@celery_app.task(bind=True, base=CallbackTask)
def generate_report_task(self, report_type: str, filters: Dict[str, Any]):
    """Generate report task"""
    try:
        logger.info(f"Generating {report_type} report")
        
        # Simulate report generation
        import time
        time.sleep(10)
        
        result = {
            "status": "generated",
            "report_type": report_type,
            "filters": filters,
            "file_path": f"/reports/{report_type}_{int(time.time())}.pdf",
            "timestamp": time.time()
        }
        
        logger.info(f"Report {report_type} generated successfully")
        return result
        
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        raise


# Task management utilities
class TaskManager:
    """Task management utilities"""
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get task status"""
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "info": result.info,
            "ready": result.ready(),
            "successful": result.successful(),
            "failed": result.failed(),
        }
    
    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """Cancel a task"""
        try:
            celery_app.control.revoke(task_id, terminate=True)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    @staticmethod
    def get_active_tasks() -> Dict[str, Any]:
        """Get active tasks"""
        try:
            inspect = celery_app.control.inspect()
            active_tasks = inspect.active()
            return active_tasks or {}
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return {}
    
    @staticmethod
    def get_worker_stats() -> Dict[str, Any]:
        """Get worker statistics"""
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            return stats or {}
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {}


# Periodic tasks (if using celery beat)
@celery_app.task(bind=True)
def periodic_cleanup_task(self):
    """Periodic cleanup task"""
    try:
        logger.info("Running periodic cleanup")
        
        # Perform cleanup operations
        cleanup_task.delay()
        
        return {"status": "scheduled", "task": "cleanup"}
        
    except Exception as exc:
        logger.error(f"Periodic cleanup failed: {exc}")
        raise


# Task scheduler
class TaskScheduler:
    """Task scheduling utilities"""
    
    @staticmethod
    def schedule_task(task_name: str, args: tuple = (), kwargs: dict = None, countdown: int = 0):
        """Schedule a task"""
        kwargs = kwargs or {}
        
        task = celery_app.send_task(
            task_name,
            args=args,
            kwargs=kwargs,
            countdown=countdown
        )
        
        return task.id
    
    @staticmethod
    def schedule_periodic_task(task_name: str, schedule_seconds: int, args: tuple = (), kwargs: dict = None):
        """Schedule a periodic task"""
        kwargs = kwargs or {}
        
        # In a real implementation, you would use celery beat for periodic tasks
        # This is a simplified example
        
        return f"periodic_{task_name}_{schedule_seconds}"


# Export task manager instance
task_manager = TaskManager()
task_scheduler = TaskScheduler()
