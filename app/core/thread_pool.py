"""
Thread pool management for concurrent operations
"""
import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)


class ThreadPoolManager:
    """Manages thread pools for different types of operations."""
    
    def __init__(self):
        self.pools: Dict[str, ThreadPoolExecutor] = {}
        self.lock = threading.Lock()
        self._default_pool_size = settings.THREAD_POOL_SIZE
        self._max_workers = settings.MAX_WORKERS
    
    def get_pool(self, pool_name: str, max_workers: Optional[int] = None) -> ThreadPoolExecutor:
        """Get or create a thread pool."""
        with self.lock:
            if pool_name not in self.pools:
                workers = max_workers or self._default_pool_size
                self.pools[pool_name] = ThreadPoolExecutor(
                    max_workers=workers,
                    thread_name_prefix=f"{pool_name}_worker"
                )
                logger.info(f"Created thread pool '{pool_name}' with {workers} workers")
            
            return self.pools[pool_name]
    
    def submit_task(
        self, 
        pool_name: str, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> asyncio.Future:
        """Submit a task to a specific thread pool."""
        pool = self.get_pool(pool_name)
        loop = asyncio.get_event_loop()
        
        def run_task():
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Task execution failed in pool '{pool_name}': {str(e)}")
                raise
        
        return loop.run_in_executor(pool, run_task)
    
    async def run_parallel_tasks(
        self,
        pool_name: str,
        tasks: List[tuple],
        max_concurrent: Optional[int] = None
    ) -> List[Any]:
        """Run multiple tasks in parallel."""
        pool = self.get_pool(pool_name)
        loop = asyncio.get_event_loop()
        
        # Limit concurrent tasks if specified
        if max_concurrent:
            semaphore = asyncio.Semaphore(max_concurrent)
        else:
            semaphore = None
        
        async def run_task(task_info):
            func, args, kwargs = task_info
            if semaphore:
                async with semaphore:
                    return await loop.run_in_executor(pool, func, *args)
            else:
                return await loop.run_in_executor(pool, func, *args)
        
        # Execute all tasks
        results = await asyncio.gather(
            *[run_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Task {i} failed: {str(result)}")
        
        return results
    
    def shutdown_pool(self, pool_name: str, wait: bool = True) -> None:
        """Shutdown a specific thread pool."""
        with self.lock:
            if pool_name in self.pools:
                pool = self.pools[pool_name]
                pool.shutdown(wait=wait)
                del self.pools[pool_name]
                logger.info(f"Shutdown thread pool '{pool_name}'")
    
    def shutdown_all_pools(self, wait: bool = True) -> None:
        """Shutdown all thread pools."""
        with self.lock:
            for pool_name, pool in self.pools.items():
                pool.shutdown(wait=wait)
                logger.info(f"Shutdown thread pool '{pool_name}'")
            self.pools.clear()
    
    @contextmanager
    def temporary_pool(self, pool_name: str, max_workers: int = 4):
        """Context manager for temporary thread pool."""
        try:
            pool = self.get_pool(pool_name, max_workers)
            yield pool
        finally:
            self.shutdown_pool(pool_name)


class AsyncTaskManager:
    """Manages asynchronous tasks and background operations."""
    
    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.lock = asyncio.Lock()
    
    async def submit_background_task(
        self,
        task_id: str,
        coro: Callable,
        *args,
        **kwargs
    ) -> str:
        """Submit a background task."""
        async with self.lock:
            if task_id in self.running_tasks:
                raise ValueError(f"Task with ID '{task_id}' is already running")
            
            # Create and start the task
            task = asyncio.create_task(coro(*args, **kwargs))
            self.running_tasks[task_id] = task
            
            # Set up completion callback
            task.add_done_callback(
                lambda t: asyncio.create_task(self._handle_task_completion(task_id, t))
            )
            
            logger.info(f"Background task '{task_id}' submitted")
            return task_id
    
    async def _handle_task_completion(self, task_id: str, task: asyncio.Task) -> None:
        """Handle task completion."""
        async with self.lock:
            try:
                if task.exception():
                    logger.error(f"Background task '{task_id}' failed: {task.exception()}")
                    self.task_results[task_id] = {"error": str(task.exception())}
                else:
                    logger.info(f"Background task '{task_id}' completed successfully")
                    self.task_results[task_id] = {"result": task.result()}
            except Exception as e:
                logger.error(f"Error handling task completion for '{task_id}': {str(e)}")
                self.task_results[task_id] = {"error": str(e)}
            finally:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a background task."""
        async with self.lock:
            if task_id in self.running_tasks:
                return {"status": "running", "task_id": task_id}
            elif task_id in self.task_results:
                result = self.task_results[task_id]
                return {"status": "completed", "task_id": task_id, **result}
            else:
                return {"status": "not_found", "task_id": task_id}
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running background task."""
        async with self.lock:
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.cancel()
                del self.running_tasks[task_id]
                logger.info(f"Background task '{task_id}' cancelled")
                return True
            return False
    
    async def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tasks."""
        async with self.lock:
            tasks = {}
            
            # Running tasks
            for task_id in self.running_tasks:
                tasks[task_id] = {"status": "running", "task_id": task_id}
            
            # Completed tasks
            for task_id, result in self.task_results.items():
                tasks[task_id] = {"status": "completed", "task_id": task_id, **result}
            
            return tasks


# Global instances
thread_pool_manager = ThreadPoolManager()
async_task_manager = AsyncTaskManager()


# Convenience functions
async def run_in_thread(func: Callable, *args, pool_name: str = "default", **kwargs) -> Any:
    """Run a function in a thread pool."""
    return await thread_pool_manager.submit_task(pool_name, func, *args, **kwargs)


async def run_cpu_intensive_task(func: Callable, *args, **kwargs) -> Any:
    """Run a CPU-intensive task in a dedicated thread pool."""
    return await thread_pool_manager.submit_task("cpu_intensive", func, *args, **kwargs)


async def run_io_intensive_task(func: Callable, *args, **kwargs) -> Any:
    """Run an I/O-intensive task in a dedicated thread pool."""
    return await thread_pool_manager.submit_task("io_intensive", func, *args, **kwargs)


async def submit_background_task(task_id: str, coro: Callable, *args, **kwargs) -> str:
    """Submit a background task."""
    return await async_task_manager.submit_background_task(task_id, coro, *args, **kwargs)


async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get background task status."""
    return await async_task_manager.get_task_status(task_id)
