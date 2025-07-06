"""
Custom decorators for common functionality
"""
import time
import logging
import functools
from typing import Any, Callable, Dict, Optional
from fastapi import HTTPException, status

from app.core.exceptions import RateLimitException, ExternalServiceException

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time."""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.4f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.4f} seconds: {str(e)}"
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} executed in {execution_time:.4f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.4f} seconds: {str(e)}"
            )
            raise
    
    # Return appropriate wrapper based on function type
    if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
        return async_wrapper
    else:
        return sync_wrapper


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator to retry function execution on failure."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {str(e)}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    
                    import asyncio
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {str(e)}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def cache_result(ttl: int = 300) -> Callable:
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Dict[str, Any]] = {}
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            if cache_key in cache:
                cache_entry = cache[cache_key]
                if time.time() - cache_entry['timestamp'] < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache_entry['value']
                else:
                    del cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = {
                'value': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            if cache_key in cache:
                cache_entry = cache[cache_key]
                if time.time() - cache_entry['timestamp'] < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache_entry['value']
                else:
                    del cache[cache_key]
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = {
                'value': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_permissions(required_permissions: list) -> Callable:
    """Decorator to validate user permissions."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # This would typically check against the current user's permissions
            # For now, we'll just log the required permissions
            logger.info(f"Function {func.__name__} requires permissions: {required_permissions}")
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def handle_external_service_errors(service_name: str) -> Callable:
    """Decorator to handle external service errors."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"External service {service_name} error: {str(e)}")
                raise ExternalServiceException(service_name, str(e))
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"External service {service_name} error: {str(e)}")
                raise ExternalServiceException(service_name, str(e))
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
