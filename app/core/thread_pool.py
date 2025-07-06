"""
Thread pool management for concurrent operations.
"""
import asyncio
import concurrent.futures
from typing import Callable, Any, List, Optional
from functools import wraps
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class ThreadPoolManager:
    """Thread pool manager for handling concurrent operations."""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or settings.MAX_WORKERS
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="FastAPI-Worker"
        )
        logger.info(f"Thread pool initialized with {self.max_workers} workers")
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """Run a function in a thread pool."""
        loop = asyncio.get_event_loop()
        
        try:
            result = await loop.run_in_executor(
                self.executor,
                lambda: func(*args, **kwargs)
            )
            return result
        except Exception as e:
            logger.error(f"Error in thread pool execution: {str(e)}")
            raise
    
    async def run_multiple_in_threads(
        self,
        tasks: List[tuple],  # List of (func, args, kwargs) tuples
        timeout: Optional[float] = None
    ) -> List[Any]:
        """Run multiple functions concurrently in thread pool."""
        loop = asyncio.get_event_loop()
        
        futures = []
        for func, args, kwargs in tasks:
            future = loop.run_in_executor(
                self.executor,
                lambda f=func, a=args, k=kwargs: f(*a, **k)
            )
            futures.append(future)
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*futures, return_exceptions=True),
                timeout=timeout
            )
            return results
        except asyncio.TimeoutError:
            logger.error("Thread pool tasks timed out")
            # Cancel pending futures
            for future in futures:
                if not future.done():
                    future.cancel()
            raise
    
    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool."""
        self.executor.shutdown(wait=wait)
        logger.info("Thread pool shutdown completed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# Global thread pool instance
thread_pool = ThreadPoolManager()


def run_in_thread(func: Callable) -> Callable:
    """Decorator to run function in thread pool."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await thread_pool.run_in_thread(func, *args, **kwargs)
    return wrapper


class AsyncBatchProcessor:
    """Async batch processor for handling bulk operations."""
    
    def __init__(self, batch_size: int = 100, max_workers: int = None):
        self.batch_size = batch_size
        self.thread_pool = ThreadPoolManager(max_workers)
    
    async def process_batch(
        self,
        items: List[Any],
        processor_func: Callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """Process items in batches."""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_tasks = [
                (processor_func, (item, *args), kwargs)
                for item in batch
            ]
            
            batch_results = await self.thread_pool.run_multiple_in_threads(
                batch_tasks
            )
            results.extend(batch_results)
        
        return results
    
    async def process_parallel_batches(
        self,
        items: List[Any],
        processor_func: Callable,
        *args,
        **kwargs
    ) -> List[Any]:
        """Process multiple batches in parallel."""
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        batch_tasks = []
        for batch in batches:
            for item in batch:
                batch_tasks.append((processor_func, (item, *args), kwargs))
        
        return await self.thread_pool.run_multiple_in_threads(batch_tasks)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.thread_pool.shutdown()


class WorkerPool:
    """Worker pool for managing background tasks."""
    
    def __init__(self, pool_size: int = None):
        self.pool_size = pool_size or settings.THREAD_POOL_SIZE
        self.workers = []
        self.task_queue = asyncio.Queue()
        self.running = False
        logger.info(f"Worker pool initialized with {self.pool_size} workers")
    
    async def start(self):
        """Start the worker pool."""
        self.running = True
        
        for i in range(self.pool_size):
            worker = asyncio.create_task(self._worker(f"Worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Started {len(self.workers)} workers")
    
    async def stop(self):
        """Stop the worker pool."""
        self.running = False
        
        # Signal all workers to stop
        for _ in self.workers:
            await self.task_queue.put(None)
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Worker pool stopped")
    
    async def submit_task(self, task_func: Callable, *args, **kwargs):
        """Submit a task to the worker pool."""
        await self.task_queue.put((task_func, args, kwargs))
    
    async def _worker(self, name: str):
        """Worker function."""
        logger.info(f"Worker {name} started")
        
        while self.running:
            try:
                task = await self.task_queue.get()
                
                if task is None:  # Shutdown signal
                    break
                
                task_func, args, kwargs = task
                
                # Execute task
                if asyncio.iscoroutinefunction(task_func):
                    await task_func(*args, **kwargs)
                else:
                    await thread_pool.run_in_thread(task_func, *args, **kwargs)
                
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker {name} error: {str(e)}")
        
        logger.info(f"Worker {name} stopped")


# Global worker pool instance
worker_pool = WorkerPool()
