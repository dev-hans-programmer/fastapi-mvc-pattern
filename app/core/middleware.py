"""
Middleware configuration and setup
"""

import time
import logging
from typing import Callable, Optional
from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uuid
from contextvars import ContextVar

from app.core.config import get_settings
from app.core.logging import log_request, log_error

settings = get_settings()
logger = logging.getLogger(__name__)

# Context variables
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to each request
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Set request ID in context
        request_id_var.set(request_id)
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get request info
        method = request.method
        url = str(request.url)
        user_agent = request.headers.get("User-Agent", "")
        remote_addr = request.client.host if request.client else "unknown"
        
        # Log request start
        logger.info(
            f"Request started: {method} {url}",
            extra={
                "method": method,
                "url": url,
                "user_agent": user_agent,
                "remote_addr": remote_addr,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful request
            log_request(
                method=method,
                url=url,
                status_code=response.status_code,
                duration=duration,
                user_id=getattr(request.state, "user_id", None),
                extra={
                    "user_agent": user_agent,
                    "remote_addr": remote_addr,
                    "request_id": getattr(request.state, "request_id", ""),
                },
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            log_error(
                error=e,
                context={
                    "method": method,
                    "url": url,
                    "duration": duration,
                    "user_agent": user_agent,
                    "remote_addr": remote_addr,
                    "request_id": getattr(request.state, "request_id", ""),
                },
                user_id=getattr(request.state, "user_id", None),
            )
            
            # Re-raise exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    """
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/", "/health/ready", "/health/live"]:
            return await call_next(request)
        
        # Check rate limit
        current_time = time.time()
        
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        # Clean old requests
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if current_time - req_time < self.period
        ]
        
        # Check if rate limit exceeded
        if len(self.clients[client_ip]) >= self.calls:
            from app.core.exceptions import RateLimitException
            raise RateLimitException(
                message=f"Rate limit exceeded. Max {self.calls} requests per {self.period} seconds",
                retry_after=self.period,
            )
        
        # Add current request
        self.clients[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(self.calls - len(self.clients[client_ip]))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.period))
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for error handling and recovery
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error
            log_error(
                error=e,
                context={
                    "method": request.method,
                    "url": str(request.url),
                    "request_id": getattr(request.state, "request_id", ""),
                },
                user_id=getattr(request.state, "user_id", None),
            )
            
            # Re-raise for proper handling by exception handlers
            raise


def setup_middleware(app: FastAPI) -> None:
    """
    Setup middleware for the FastAPI application
    """
    # Add compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add trusted host middleware (only in production)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # Configure based on your needs
        )
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        max_age=3600,  # 1 hour
    )
    
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.RATE_LIMIT_REQUESTS,
        period=settings.RATE_LIMIT_WINDOW,
    )
    
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add request ID middleware (should be first)
    app.add_middleware(RequestIDMiddleware)
    
    logger.info("Middleware setup complete")


def get_request_id() -> str:
    """
    Get current request ID from context
    """
    return request_id_var.get()


def get_user_id() -> Optional[str]:
    """
    Get current user ID from context
    """
    return user_id_var.get()


def set_user_id(user_id: str) -> None:
    """
    Set user ID in context
    """
    user_id_var.set(user_id)
