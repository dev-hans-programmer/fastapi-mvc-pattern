"""
Common decorators for the application
"""
import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, Optional
from fastapi import HTTPException, status

from app.core.exceptions import RateLimitError, ValidationError
from app.core.security import SecurityUtils

logger = logging.getLogger(__name__)


def timer(func: Callable) -> Callable:
    """Decorator to measure execution time"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for retrying failed operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"{func.__name__} failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"{func.__name__} failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def cache(ttl: int = 300):
    """Simple in-memory caching decorator"""
    def decorator(func: Callable) -> Callable:
        cache_storage = {}
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # Check cache
            if cache_key in cache_storage:
                cached_result, timestamp = cache_storage[cache_key]
                if current_time - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_storage[cache_key] = (result, current_time)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # Check cache
            if cache_key in cache_storage:
                cached_result, timestamp = cache_storage[cache_key]
                if current_time - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_storage[cache_key] = (result, current_time)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def rate_limit(max_calls: int = 100, window: int = 60):
    """Rate limiting decorator"""
    def decorator(func: Callable) -> Callable:
        call_history = {}
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get caller identifier (this is simplified)
            caller_id = str(args) + str(kwargs)
            current_time = time.time()
            
            # Clean old calls
            if caller_id in call_history:
                call_history[caller_id] = [
                    call_time for call_time in call_history[caller_id]
                    if current_time - call_time < window
                ]
            else:
                call_history[caller_id] = []
            
            # Check rate limit
            if len(call_history[caller_id]) >= max_calls:
                raise RateLimitError(f"Rate limit exceeded for {func.__name__}")
            
            # Record call
            call_history[caller_id].append(current_time)
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Get caller identifier (this is simplified)
            caller_id = str(args) + str(kwargs)
            current_time = time.time()
            
            # Clean old calls
            if caller_id in call_history:
                call_history[caller_id] = [
                    call_time for call_time in call_history[caller_id]
                    if current_time - call_time < window
                ]
            else:
                call_history[caller_id] = []
            
            # Check rate limit
            if len(call_history[caller_id]) >= max_calls:
                raise RateLimitError(f"Rate limit exceeded for {func.__name__}")
            
            # Record call
            call_history[caller_id].append(current_time)
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_input(schema: type):
    """Input validation decorator"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Validate input using Pydantic schema
            try:
                if 'data' in kwargs:
                    validated_data = schema(**kwargs['data'])
                    kwargs['data'] = validated_data
                
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Input validation failed for {func.__name__}: {e}")
                raise ValidationError(f"Invalid input: {e}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Validate input using Pydantic schema
            try:
                if 'data' in kwargs:
                    validated_data = schema(**kwargs['data'])
                    kwargs['data'] = validated_data
                
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Input validation failed for {func.__name__}: {e}")
                raise ValidationError(f"Invalid input: {e}")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def log_execution(log_level: str = "INFO"):
    """Decorator to log function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            log_method = getattr(logger, log_level.lower())
            log_method(f"Executing {func.__name__} with args: {args}, kwargs: {kwargs}")
            
            try:
                result = await func(*args, **kwargs)
                log_method(f"Successfully executed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error executing {func.__name__}: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            log_method = getattr(logger, log_level.lower())
            log_method(f"Executing {func.__name__} with args: {args}, kwargs: {kwargs}")
            
            try:
                result = func(*args, **kwargs)
                log_method(f"Successfully executed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error executing {func.__name__}: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def require_permission(permission: str):
    """Decorator to require specific permissions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a simplified example
            # In a real application, you would check the user's permissions
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check permissions (simplified)
            if not hasattr(user, 'permissions') or permission not in user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_role(role: str):
    """Decorator to require specific roles"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a simplified example
            # In a real application, you would check the user's roles
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check role (simplified)
            if not hasattr(user, 'role') or user.role != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def handle_exceptions(default_response: Any = None):
    """Decorator to handle exceptions gracefully"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {e}")
                if default_response is not None:
                    return default_response
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception in {func.__name__}: {e}")
                if default_response is not None:
                    return default_response
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def sanitize_input(fields: list):
    """Decorator to sanitize input fields"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Sanitize specified fields
            for field in fields:
                if field in kwargs:
                    if isinstance(kwargs[field], str):
                        kwargs[field] = kwargs[field].strip()
                        # Remove potentially dangerous characters
                        dangerous_chars = ["<", ">", "&", '"', "'"]
                        for char in dangerous_chars:
                            kwargs[field] = kwargs[field].replace(char, "")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
