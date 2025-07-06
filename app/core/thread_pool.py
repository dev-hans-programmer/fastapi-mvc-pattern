"""
Thread pool management for multi-threading operations
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from functools import wraps
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """
    Task status enumeration
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """
    Task information dataclass
    """
    task_id: str
    function_name: str
    args: tuple
    kwargs: dict
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    duration: Optional[float] = None


class ThreadPoolManager:
    """
    Thread pool manager for handling concurrent operations
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or settings.THREAD_POOL_MAX_WORKERS
        self.executor: Optional[ThreadPoolExecutor] = None
        self.tasks: Dict[str, TaskInfo] = {}
        self.futures: Dict[str, Future] = {}
        self.lock = threading.Lock()
        self.running = False
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "active_tasks": 0,
        }
    
    async def start(self):
        """
        Start the thread pool manager
        """
        if self.running:
            logger.warning("Thread pool manager is already running")
            return
        
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.running = True
        
        logger.info(f"Thread pool manager started with {self.max_workers} workers")
    
    async def stop(self):
        """
        Stop the thread pool manager
        """
        if not self.running:
            logger.warning("Thread pool manager is not running")
            return
        
        self.running = False
        
        # Cancel all pending tasks
        with self.lock:
            for task_id, future in self.futures.items():
                if not future.done():
                    future.cancel()
                    self.tasks[task_id].status = TaskStatus.CANCELLED
                    self.stats["cancelled_tasks"] += 1
        
        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
        
        logger.info("Thread pool manager stopped")
    
    def submit_task(
        self,
        function: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Submit a task to the thread pool
        """
        if not self.running or not self.executor:
            raise RuntimeError("Thread pool manager is not running")
        
        # Generate task ID if not provided
        if not task_id:
            task_id = f"task_{int(time.time() * 1000000)}"
        
        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            function_name=function.__name__,
            args=args,
            kwargs=kwargs,
        )
        
        # Submit task to executor
        future = self.executor.submit(self._execute_task, task_info, function)
        
        # Store task info and future
        with self.lock:
            self.tasks[task_id] = task_info
            self.futures[task_id] = future
            self.stats["total_tasks"] += 1
            self.stats["active_tasks"] += 1
        
        logger.info(f"Task submitted: {task_id} ({function.__name__})")
        
        return task_id
    
    def _execute_task(self, task_info: TaskInfo, function: Callable) -> Any:
        """
        Execute a task and update its status
        """
        task_info.started_at = time.time()
        task_info.status = TaskStatus.RUNNING
        
        try:
            logger.info(f"Executing task: {task_info.task_id}")
            
            # Execute the function
            result = function(*task_info.args, **task_info.kwargs)
            
            # Update task info
            task_info.completed_at = time.time()
            task_info.duration = task_info.completed_at - task_info.started_at
            task_info.result = result
            task_info.status = TaskStatus.COMPLETED
            
            with self.lock:
                self.stats["completed_tasks"] += 1
                self.stats["active_tasks"] -= 1
            
            logger.info(f"Task completed: {task_info.task_id} ({task_info.duration:.3f}s)")
            
            return result
            
        except Exception as e:
            # Update task info
            task_info.completed_at = time.time()
            task_info.duration = task_info.completed_at - task_info.started_at
            task_info.error = str(e)
            task_info.status = TaskStatus.FAILED
            
            with self.lock:
                self.stats["failed_tasks"] += 1
                self.stats["active_tasks"] -= 1
            
            logger.error(f"Task failed: {task_info.task_id} - {e}")
            
            raise
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get task status
        """
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get task result
        """
        with self.lock:
            future = self.futures.get(task_id)
            if not future:
                raise ValueError(f"Task not found: {task_id}")
        
        return future.result(timeout=timeout)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task
        """
        with self.lock:
            future = self.futures.get(task_id)
            if not future:
                return False
            
            if future.cancel():
                self.tasks[task_id].status = TaskStatus.CANCELLED
                self.stats["cancelled_tasks"] += 1
                self.stats["active_tasks"] -= 1
                logger.info(f"Task cancelled: {task_id}")
                return True
            
            return False
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """
        Get all tasks
        """
        with self.lock:
            return list(self.tasks.values())
    
    def get_active_tasks(self) -> List[TaskInfo]:
        """
        Get active tasks
        """
        with self.lock:
            return [
                task for task in self.tasks.values()
                if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
            ]
    
    def get_completed_tasks(self) -> List[TaskInfo]:
        """
        Get completed tasks
        """
        with self.lock:
            return [
                task for task in self.tasks.values()
                if task.status == TaskStatus.COMPLETED
            ]
    
    def get_failed_tasks(self) -> List[TaskInfo]:
        """
        Get failed tasks
        """
        with self.lock:
            return [
                task for task in self.tasks.values()
                if task.status == TaskStatus.FAILED
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get thread pool statistics
        """
        with self.lock:
            return {
                **self.stats,
                "max_workers": self.max_workers,
                "running": self.running,
                "total_tasks_in_memory": len(self.tasks),
            }
    
    def clear_completed_tasks(self, older_than_seconds: int = 3600):
        """
        Clear completed tasks older than specified seconds
        """
        current_time = time.time()
        cleared_count = 0
        
        with self.lock:
            tasks_to_remove = []
            
            for task_id, task_info in self.tasks.items():
                if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task_info.completed_at and
                    current_time - task_info.completed_at > older_than_seconds):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                if task_id in self.futures:
                    del self.futures[task_id]
                cleared_count += 1
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} completed tasks")
        
        return cleared_count
    
    async def wait_for_tasks(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for multiple tasks to complete
        """
        if not task_ids:
            return {}
        
        futures_to_wait = {}
        
        with self.lock:
            for task_id in task_ids:
                future = self.futures.get(task_id)
                if future:
                    futures_to_wait[task_id] = future
        
        results = {}
        
        # Wait for futures to complete
        for task_id, future in futures_to_wait.items():
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, future.result, timeout
                )
                results[task_id] = {"success": True, "result": result}
            except Exception as e:
                results[task_id] = {"success": False, "error": str(e)}
        
        return results
    
    def submit_batch_tasks(
        self,
        function: Callable,
        args_list: List[tuple],
        kwargs_list: Optional[List[dict]] = None,
    ) -> List[str]:
        """
        Submit batch tasks
        """
        if not kwargs_list:
            kwargs_list = [{}] * len(args_list)
        
        if len(args_list) != len(kwargs_list):
            raise ValueError("args_list and kwargs_list must have the same length")
        
        task_ids = []
        
        for i, (args, kwargs) in enumerate(zip(args_list, kwargs_list)):
            task_id = self.submit_task(function, *args, **kwargs)
            task_ids.append(task_id)
        
        logger.info(f"Submitted {len(task_ids)} batch tasks")
        
        return task_ids


# Global thread pool manager instance
thread_pool_manager = ThreadPoolManager()


def async_task(timeout: Optional[float] = None):
    """
    Decorator to run a function in thread pool
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Submit task to thread pool
            task_id = thread_pool_manager.submit_task(func, *args, **kwargs)
            
            # Wait for result
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: thread_pool_manager.get_task_result(task_id, timeout)
                )
                return result
            except Exception as e:
                logger.error(f"Async task failed: {func.__name__} - {e}")
                raise
        
        return wrapper
    return decorator


def batch_process(
    function: Callable,
    items: List[Any],
    batch_size: int = 10,
    timeout: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Process items in batches using thread pool
    """
    if not items:
        return []
    
    # Create batches
    batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    # Submit batch tasks
    task_ids = []
    for batch in batches:
        for item in batch:
            task_id = thread_pool_manager.submit_task(function, item)
            task_ids.append(task_id)
    
    # Wait for all tasks to complete
    results = []
    for task_id in task_ids:
        try:
            result = thread_pool_manager.get_task_result(task_id, timeout)
            results.append({"success": True, "result": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    return results


@contextmanager
def thread_pool_context(max_workers: Optional[int] = None):
    """
    Context manager for thread pool
    """
    manager = ThreadPoolManager(max_workers)
    
    try:
        asyncio.run(manager.start())
        yield manager
    finally:
        asyncio.run(manager.stop())


# Utility functions
def cpu_bound_task(data: Any) -> Any:
    """
    Example CPU-bound task
    """
    import hashlib
    import json
    
    # Simulate CPU-intensive work
    for i in range(1000):
        hash_object = hashlib.md5(json.dumps(data, default=str).encode())
        result = hash_object.hexdigest()
    
    return result


def io_bound_task(url: str) -> Dict[str, Any]:
    """
    Example I/O-bound task
    """
    import requests
    import time
    
    start_time = time.time()
    
    try:
        response = requests.get(url, timeout=10)
        duration = time.time() - start_time
        
        return {
            "url": url,
            "status_code": response.status_code,
            "duration": duration,
            "success": True,
        }
    except Exception as e:
        duration = time.time() - start_time
        
        return {
            "url": url,
            "error": str(e),
            "duration": duration,
            "success": False,
        }


def data_processing_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example data processing task
    """
    import time
    
    # Simulate data processing
    time.sleep(0.1)
    
    processed_data = {
        "original_data": data,
        "processed_at": time.time(),
        "row_count": len(data) if isinstance(data, (list, dict)) else 1,
        "processing_status": "completed",
    }
    
    return processed_data
