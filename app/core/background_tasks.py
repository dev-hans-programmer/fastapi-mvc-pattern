"""
Background task processing with Celery
"""

import logging
from typing import Any, Dict, Optional, Callable
from celery import Celery
from celery.result import AsyncResult
from celery.exceptions import Retry, WorkerLostError
from datetime import datetime, timedelta
import asyncio
import json

from app.core.config import get_settings
from app.core.logging import log_background_task

settings = get_settings()
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "fastapi_backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.core.background_tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "app.core.background_tasks.send_email": {"queue": "email"},
        "app.core.background_tasks.process_file": {"queue": "file_processing"},
        "app.core.background_tasks.generate_report": {"queue": "reports"},
        "app.core.background_tasks.cleanup_task": {"queue": "cleanup"},
    },
)


class TaskStatus:
    """
    Task status constants
    """
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"


class BackgroundTaskManager:
    """
    Background task manager
    """
    
    def __init__(self):
        self.celery_app = celery_app
    
    def submit_task(
        self,
        task_name: str,
        *args,
        **kwargs
    ) -> str:
        """
        Submit a background task
        """
        try:
            result = self.celery_app.send_task(task_name, args, kwargs)
            logger.info(f"Task submitted: {task_name} [{result.id}]")
            return result.id
        except Exception as e:
            logger.error(f"Failed to submit task {task_name}: {e}")
            raise
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            status_info = {
                "task_id": task_id,
                "status": result.status,
                "result": result.result,
                "traceback": result.traceback,
                "date_done": result.date_done,
                "successful": result.successful(),
                "failed": result.failed(),
            }
            
            if result.status == TaskStatus.STARTED:
                status_info["info"] = result.info
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "error": str(e),
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task
        """
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Task cancelled: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def get_active_tasks(self) -> Dict[str, Any]:
        """
        Get active tasks
        """
        try:
            inspect = self.celery_app.control.inspect()
            return {
                "active": inspect.active(),
                "scheduled": inspect.scheduled(),
                "reserved": inspect.reserved(),
            }
        except Exception as e:
            logger.error(f"Failed to get active tasks: {e}")
            return {}
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get worker statistics
        """
        try:
            inspect = self.celery_app.control.inspect()
            return {
                "stats": inspect.stats(),
                "registered": inspect.registered(),
                "ping": inspect.ping(),
            }
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {}


# Global task manager instance
task_manager = BackgroundTaskManager()


# Task decorators and utilities
def task_wrapper(name: str, bind: bool = True, retry_kwargs: Optional[Dict] = None):
    """
    Decorator for creating Celery tasks with logging
    """
    def decorator(func: Callable) -> Callable:
        @celery_app.task(name=name, bind=bind)
        def wrapper(self, *args, **kwargs):
            task_id = self.request.id
            start_time = datetime.now()
            
            try:
                log_background_task(
                    task_name=name,
                    task_id=task_id,
                    status="STARTED",
                    extra={"args": args, "kwargs": kwargs}
                )
                
                # Execute the task
                result = func(*args, **kwargs)
                
                duration = (datetime.now() - start_time).total_seconds()
                log_background_task(
                    task_name=name,
                    task_id=task_id,
                    status="SUCCESS",
                    duration=duration,
                    extra={"result": result}
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                log_background_task(
                    task_name=name,
                    task_id=task_id,
                    status="FAILURE",
                    duration=duration,
                    extra={"error": str(e)}
                )
                
                # Retry logic
                if retry_kwargs:
                    try:
                        raise self.retry(exc=e, **retry_kwargs)
                    except Retry:
                        raise
                
                raise
        
        return wrapper
    return decorator


# Background tasks
@task_wrapper("app.core.background_tasks.send_email")
def send_email(
    to_email: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html_body: Optional[str] = None,
    attachments: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Send email task
    """
    try:
        # Simulate email sending
        import time
        time.sleep(2)  # Simulate processing time
        
        logger.info(f"Email sent to {to_email}: {subject}")
        
        return {
            "status": "sent",
            "to_email": to_email,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise


@task_wrapper("app.core.background_tasks.process_file")
def process_file(
    file_path: str,
    processing_type: str,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process file task
    """
    try:
        # Simulate file processing
        import time
        time.sleep(5)  # Simulate processing time
        
        logger.info(f"File processed: {file_path} ({processing_type})")
        
        return {
            "status": "processed",
            "file_path": file_path,
            "processing_type": processing_type,
            "options": options,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {e}")
        raise


@task_wrapper("app.core.background_tasks.generate_report")
def generate_report(
    report_type: str,
    parameters: Dict[str, Any],
    user_id: str,
    format: str = "pdf",
) -> Dict[str, Any]:
    """
    Generate report task
    """
    try:
        # Simulate report generation
        import time
        time.sleep(10)  # Simulate processing time
        
        report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Report generated: {report_id} ({report_type})")
        
        return {
            "status": "generated",
            "report_id": report_id,
            "report_type": report_type,
            "format": format,
            "user_id": user_id,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to generate report {report_type}: {e}")
        raise


@task_wrapper("app.core.background_tasks.cleanup_task")
def cleanup_task(
    cleanup_type: str,
    older_than_days: int = 30,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Cleanup task
    """
    try:
        # Simulate cleanup
        import time
        time.sleep(3)  # Simulate processing time
        
        cleaned_items = 0
        
        if cleanup_type == "logs":
            cleaned_items = 15
        elif cleanup_type == "temp_files":
            cleaned_items = 32
        elif cleanup_type == "sessions":
            cleaned_items = 8
        
        logger.info(f"Cleanup completed: {cleanup_type} ({cleaned_items} items)")
        
        return {
            "status": "completed",
            "cleanup_type": cleanup_type,
            "older_than_days": older_than_days,
            "dry_run": dry_run,
            "cleaned_items": cleaned_items,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup {cleanup_type}: {e}")
        raise


@task_wrapper("app.core.background_tasks.sync_external_data")
def sync_external_data(
    source: str,
    sync_type: str,
    last_sync: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sync external data task
    """
    try:
        # Simulate data sync
        import time
        time.sleep(8)  # Simulate processing time
        
        synced_records = 0
        
        if source == "api":
            synced_records = 120
        elif source == "database":
            synced_records = 45
        elif source == "file":
            synced_records = 78
        
        logger.info(f"Data sync completed: {source} ({synced_records} records)")
        
        return {
            "status": "completed",
            "source": source,
            "sync_type": sync_type,
            "last_sync": last_sync,
            "synced_records": synced_records,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to sync data from {source}: {e}")
        raise


# Periodic tasks
@celery_app.task(name="app.core.background_tasks.daily_cleanup")
def daily_cleanup():
    """
    Daily cleanup task
    """
    try:
        # Run various cleanup tasks
        cleanup_results = []
        
        # Cleanup logs
        result = cleanup_task.delay("logs", older_than_days=7)
        cleanup_results.append({"type": "logs", "task_id": result.id})
        
        # Cleanup temp files
        result = cleanup_task.delay("temp_files", older_than_days=1)
        cleanup_results.append({"type": "temp_files", "task_id": result.id})
        
        # Cleanup sessions
        result = cleanup_task.delay("sessions", older_than_days=30)
        cleanup_results.append({"type": "sessions", "task_id": result.id})
        
        logger.info(f"Daily cleanup initiated: {len(cleanup_results)} tasks")
        
        return {
            "status": "initiated",
            "cleanup_tasks": cleanup_results,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to run daily cleanup: {e}")
        raise


# Setup periodic tasks
def setup_periodic_tasks():
    """
    Setup periodic tasks
    """
    from celery.schedules import crontab
    
    celery_app.conf.beat_schedule = {
        "daily-cleanup": {
            "task": "app.core.background_tasks.daily_cleanup",
            "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
        },
        "sync-external-data": {
            "task": "app.core.background_tasks.sync_external_data",
            "schedule": crontab(minute=0),  # Run every hour
            "args": ("api", "incremental"),
        },
    }
    
    logger.info("Periodic tasks configured")


def setup_background_tasks():
    """
    Setup background tasks
    """
    try:
        # Setup periodic tasks
        setup_periodic_tasks()
        
        logger.info("Background tasks setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup background tasks: {e}")
        raise


# Utility functions
def submit_email_task(
    to_email: str,
    subject: str,
    body: str,
    **kwargs
) -> str:
    """
    Submit email task
    """
    return task_manager.submit_task(
        "app.core.background_tasks.send_email",
        to_email,
        subject,
        body,
        **kwargs
    )


def submit_file_processing_task(
    file_path: str,
    processing_type: str,
    options: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Submit file processing task
    """
    return task_manager.submit_task(
        "app.core.background_tasks.process_file",
        file_path,
        processing_type,
        options
    )


def submit_report_generation_task(
    report_type: str,
    parameters: Dict[str, Any],
    user_id: str,
    format: str = "pdf",
) -> str:
    """
    Submit report generation task
    """
    return task_manager.submit_task(
        "app.core.background_tasks.generate_report",
        report_type,
        parameters,
        user_id,
        format
    )


def get_task_result(task_id: str) -> Dict[str, Any]:
    """
    Get task result
    """
    return task_manager.get_task_status(task_id)


def cancel_task(task_id: str) -> bool:
    """
    Cancel task
    """
    return task_manager.cancel_task(task_id)
