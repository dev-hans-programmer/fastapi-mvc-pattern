"""
Dependency injection and common dependencies
"""

import logging
from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.database import get_async_db
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import verify_token
from app.core.middleware import set_user_id

settings = get_settings()
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency
    """
    async with get_async_db() as session:
        yield session


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Get current user from token (optional)
    """
    if not credentials:
        return None
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # Set user ID in context
        set_user_id(user_id)
        request.state.user_id = user_id
        
        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", []),
        }
        
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


async def get_current_user(
    current_user: Optional[dict] = Depends(get_current_user_optional),
) -> dict:
    """
    Get current authenticated user (required)
    """
    if not current_user:
        raise AuthenticationException("Authentication required")
    
    return current_user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current active user
    """
    if not current_user.get("is_active", True):
        raise AuthenticationException("User account is inactive")
    
    return current_user


async def get_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current admin user
    """
    if current_user.get("role") != "admin":
        raise AuthorizationException("Admin access required")
    
    return current_user


async def get_user_with_permission(permission: str):
    """
    Create dependency for checking user permissions
    """
    async def check_permission(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions:
            raise AuthorizationException(f"Permission required: {permission}")
        return current_user
    
    return check_permission


async def get_pagination_params(
    page: int = 1,
    limit: int = 10,
    max_limit: int = 100,
) -> dict:
    """
    Get pagination parameters
    """
    if page < 1:
        page = 1
    
    if limit < 1:
        limit = 10
    elif limit > max_limit:
        limit = max_limit
    
    offset = (page - 1) * limit
    
    return {
        "page": page,
        "limit": limit,
        "offset": offset,
    }


async def get_sorting_params(
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> dict:
    """
    Get sorting parameters
    """
    if sort_order not in ["asc", "desc"]:
        sort_order = "asc"
    
    return {
        "sort_by": sort_by,
        "sort_order": sort_order,
    }


async def get_filtering_params(
    q: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
) -> dict:
    """
    Get filtering parameters
    """
    filters = {}
    
    if q:
        filters["search"] = q
    
    if status:
        filters["status"] = status
    
    if category:
        filters["category"] = category
    
    if created_after:
        filters["created_after"] = created_after
    
    if created_before:
        filters["created_before"] = created_before
    
    return filters


async def get_request_info(request: Request) -> dict:
    """
    Get request information
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else None,
        "user_agent": request.headers.get("User-Agent"),
        "request_id": getattr(request.state, "request_id", None),
    }


async def validate_content_type(
    request: Request,
    content_type: str = "application/json",
) -> None:
    """
    Validate request content type
    """
    request_content_type = request.headers.get("Content-Type", "")
    
    if content_type not in request_content_type:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type. Expected: {content_type}",
        )


async def get_rate_limit_info(
    request: Request,
    x_ratelimit_limit: Optional[str] = Header(None),
    x_ratelimit_remaining: Optional[str] = Header(None),
    x_ratelimit_reset: Optional[str] = Header(None),
) -> dict:
    """
    Get rate limit information
    """
    return {
        "limit": int(x_ratelimit_limit) if x_ratelimit_limit else None,
        "remaining": int(x_ratelimit_remaining) if x_ratelimit_remaining else None,
        "reset": int(x_ratelimit_reset) if x_ratelimit_reset else None,
    }


class DatabaseDependency:
    """
    Database dependency class for dependency injection
    """
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __call__(self) -> AsyncSession:
        """
        Get database session
        """
        if not self.session:
            async with get_async_db() as session:
                self.session = session
                return session
        
        return self.session


class CacheDependency:
    """
    Cache dependency class for dependency injection
    """
    
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache
        """
        return self.cache.get(key)
    
    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        """
        Set value in cache
        """
        self.cache[key] = value
        # Note: This is a simple in-memory cache
        # In production, use Redis or similar
    
    async def delete(self, key: str) -> None:
        """
        Delete value from cache
        """
        self.cache.pop(key, None)


# Dependency instances
get_cache = CacheDependency()


async def get_service_dependencies() -> dict:
    """
    Get common service dependencies
    """
    return {
        "cache": get_cache,
        "settings": settings,
        "logger": logger,
    }


def require_permissions(*permissions: str):
    """
    Decorator to require specific permissions
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise AuthenticationException("Authentication required")
            
            user_permissions = current_user.get("permissions", [])
            missing_permissions = [p for p in permissions if p not in user_permissions]
            
            if missing_permissions:
                raise AuthorizationException(
                    f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(*roles: str):
    """
    Decorator to require specific roles
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise AuthenticationException("Authentication required")
            
            user_role = current_user.get("role")
            if user_role not in roles:
                raise AuthorizationException(
                    f"Required role: {' or '.join(roles)}, got: {user_role}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
