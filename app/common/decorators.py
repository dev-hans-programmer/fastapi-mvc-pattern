"""
Common decorators for the application
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timezone

from app.core.exceptions import BaseAPIException
from app.core.logging import log_error, log_execution_time

logger = logging.getLogger(__name__)


def handle_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle exceptions in controller methods
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except BaseAPIException:
            # Re-raise API exceptions as-is
            raise
        except Exception as e:
            # Log unexpected exceptions
            log_error(e, context={
                "function": func.__name__,
                "module": func.__module__,
                "args": str(args),
                "kwargs": str(kwargs),
            })
            # Convert to generic API exception
            raise BaseAPIException(
                message="An unexpected error occurred",
                status_code=500,
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e)}
            )
    
    return wrapper


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log execution time of functions
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            log_execution_time(
                function_name=func.__name__,
                duration=duration,
                success=True,
                extra={
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            log_execution_time(
                function_name=func.__name__,
                duration=duration,
                success=False,
                extra={
                    "module": func.__module__,
                    "error": str(e),
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            log_execution_time(
                function_name=func.__name__,
                duration=duration,
                success=True,
                extra={
                    "module": func.__module__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            log_execution_time(
                function_name=func.__name__,
                duration=duration,
                success=False,
                extra={
                    "module": func.__module__,
                    "error": str(e),
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)) -> Callable:
    """
    Decorator to retry function execution on failure
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "final_error": str(e),
                            }
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}: {e}. Retrying in {current_delay}s",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": current_delay,
                            "error": str(e),
                        }
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time as sync_time
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}",
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "final_error": str(e),
                            }
                        )
                        raise
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}: {e}. Retrying in {current_delay}s",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "delay": current_delay,
                            "error": str(e),
                        }
                    )
                    
                    sync_time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def cache_result(ttl: int = 300, key_prefix: Optional[str] = None) -> Callable:
    """
    Decorator to cache function results
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        def generate_cache_key(*args, **kwargs) -> str:
            """Generate cache key from function arguments"""
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            return ":".join(key_parts)
        
        def is_cache_valid(cache_key: str) -> bool:
            """Check if cache entry is still valid"""
            if cache_key not in cache_times:
                return False
            return time.time() - cache_times[cache_key] < ttl
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = generate_cache_key(*args, **kwargs)
            
            # Check cache
            if cache_key in cache and is_cache_valid(cache_key):
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cache[cache_key]
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = result
            cache_times[cache_key] = time.time()
            
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = generate_cache_key(*args, **kwargs)
            
            # Check cache
            if cache_key in cache and is_cache_valid(cache_key):
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cache[cache_key]
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = result
            cache_times[cache_key] = time.time()
            
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_input(**validators) -> Callable:
    """
    Decorator to validate function inputs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Validate kwargs
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for parameter {param_name}: {value}")
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Validate kwargs
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for parameter {param_name}: {value}")
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def rate_limit(calls: int = 10, period: int = 60) -> Callable:
    """
    Decorator to rate limit function calls
    """
    def decorator(func: Callable) -> Callable:
        call_times = []
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Clean old call times
            call_times[:] = [t for t in call_times if current_time - t < period]
            
            # Check rate limit
            if len(call_times) >= calls:
                raise BaseAPIException(
                    message=f"Rate limit exceeded: {calls} calls per {period} seconds",
                    status_code=429,
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # Add current call time
            call_times.append(current_time)
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Clean old call times
            call_times[:] = [t for t in call_times if current_time - t < period]
            
            # Check rate limit
            if len(call_times) >= calls:
                raise BaseAPIException(
                    message=f"Rate limit exceeded: {calls} calls per {period} seconds",
                    status_code=429,
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            # Add current call time
            call_times.append(current_time)
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # This would typically check for authentication
        # For now, it's a placeholder
        return await func(*args, **kwargs)
    
    return wrapper


def benchmark(func: Callable) -> Callable:
    """
    Decorator to benchmark function execution
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = 0  # Would use memory profiling library in production
        
        try:
            result = await func(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(
                f"Benchmark - {func.__name__}: {duration:.4f}s",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(
                f"Benchmark - {func.__name__} failed after {duration:.4f}s: {e}",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "error": str(e),
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(
                f"Benchmark - {func.__name__}: {duration:.4f}s",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            logger.error(
                f"Benchmark - {func.__name__} failed after {duration:.4f}s: {e}",
                extra={
                    "function": func.__name__,
                    "duration": duration,
                    "error": str(e),
                    "args_count": len(args),
                    "kwargs_count": len(kwargs),
                }
            )
            
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
