"""
Utility decorators for the application.
"""
import functools
import time
import logging
from typing import Callable, Any, Dict, Optional
from datetime import datetime, timedelta

from app.core.exceptions import RateLimitException, ValidationException

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator for functions that might fail.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}"
                    )
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


def cache_result(ttl_seconds: int = 300):
    """
    Simple in-memory cache decorator.
    
    Args:
        ttl_seconds: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Check if result is in cache and not expired
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=ttl_seconds):
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                else:
                    # Remove expired entry
                    del cache[cache_key]
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, datetime.utcnow())
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            
            return result
        
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = 60):
    """
    Rate limiting decorator.
    
    Args:
        requests_per_minute: Maximum requests allowed per minute
    """
    def decorator(func: Callable) -> Callable:
        request_times = []
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Remove requests older than 1 minute
            cutoff_time = current_time - 60
            request_times[:] = [t for t in request_times if t > cutoff_time]
            
            # Check rate limit
            if len(request_times) >= requests_per_minute:
                logger.warning(f"Rate limit exceeded for {func.__name__}")
                raise RateLimitException(f"Rate limit of {requests_per_minute} requests per minute exceeded")
            
            # Add current request time
            request_times.append(current_time)
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def measure_time(log_level: int = logging.INFO):
    """
    Decorator to measure and log function execution time.
    
    Args:
        log_level: Logging level for the timing message
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log(
                    log_level,
                    f"{func.__name__} executed in {execution_time:.3f} seconds"
                )
                
                return result
            
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {execution_time:.3f} seconds: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator


def validate_input(**validators):
    """
    Input validation decorator.
    
    Args:
        **validators: Dictionary of parameter names and their validation functions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate parameters
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    
                    try:
                        if not validator(value):
                            raise ValidationException(f"Validation failed for parameter '{param_name}'")
                    except Exception as e:
                        raise ValidationException(f"Validation error for parameter '{param_name}': {str(e)}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_exceptions(logger_instance: Optional[logging.Logger] = None):
    """
    Decorator to log exceptions with detailed information.
    
    Args:
        logger_instance: Optional logger instance to use
    """
    def decorator(func: Callable) -> Callable:
        nonlocal logger_instance
        if logger_instance is None:
            logger_instance = logging.getLogger(func.__module__)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger_instance.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    extra={
                        "function": func.__name__,
                        "module": func.__module__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                        "exception_type": type(e).__name__,
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def require_permissions(*required_permissions):
    """
    Decorator to check user permissions.
    
    Args:
        *required_permissions: List of required permissions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This would typically integrate with your authentication system
            # For now, it's a placeholder implementation
            
            # In a real application, you would:
            # 1. Get current user from context
            # 2. Check user permissions against required_permissions
            # 3. Raise AuthorizationException if insufficient permissions
            
            logger.debug(f"Checking permissions {required_permissions} for {func.__name__}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def deprecated(message: str = "This function is deprecated"):
    """
    Decorator to mark functions as deprecated.
    
    Args:
        message: Deprecation message
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(
                f"{func.__name__} is deprecated. {message}",
                DeprecationWarning,
                stacklevel=2
            )
            logger.warning(f"Using deprecated function {func.__name__}: {message}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Circuit breaker decorator to prevent cascading failures.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Timeout in seconds before attempting recovery
        expected_exception: Exception type that triggers the circuit breaker
    """
    def decorator(func: Callable) -> Callable:
        state = {"failures": 0, "last_failure_time": None, "state": "closed"}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Check if circuit is open
            if state["state"] == "open":
                if current_time - state["last_failure_time"] < recovery_timeout:
                    logger.warning(f"Circuit breaker open for {func.__name__}")
                    raise Exception("Circuit breaker is open")
                else:
                    # Move to half-open state
                    state["state"] = "half-open"
                    logger.info(f"Circuit breaker half-open for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                
                # Reset on success
                if state["state"] == "half-open":
                    state["state"] = "closed"
                    state["failures"] = 0
                    logger.info(f"Circuit breaker closed for {func.__name__}")
                
                return result
            
            except expected_exception as e:
                state["failures"] += 1
                state["last_failure_time"] = current_time
                
                if state["failures"] >= failure_threshold:
                    state["state"] = "open"
                    logger.error(f"Circuit breaker opened for {func.__name__}")
                
                raise
        
        return wrapper
    return decorator


def async_timeout(timeout_seconds: float = 30.0):
    """
    Decorator to add timeout to async functions.
    
    Args:
        timeout_seconds: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                raise Exception(f"Function timed out after {timeout_seconds} seconds")
        
        return wrapper
    return decorator
