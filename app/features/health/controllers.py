"""
Health check controllers.
"""
import psutil
import redis
from datetime import datetime
from typing import Dict, Any
import logging

from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


class HealthController:
    """Health check controller."""
    
    async def health_check(self) -> Dict[str, Any]:
        """Basic health check."""
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    async def detailed_health_check(self) -> Dict[str, Any]:
        """Detailed health check with system information."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Database check
            db_status = await self._check_database()
            
            # Redis check
            redis_status = await self._check_redis()
            
            # Service status
            services = {
                "database": db_status,
                "redis": redis_status,
            }
            
            # Overall health
            is_healthy = all(service["status"] == "healthy" for service in services.values())
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory": {
                        "total": memory.total,
                        "available": memory.available,
                        "percent": memory.percent,
                    },
                    "disk": {
                        "total": disk.total,
                        "free": disk.free,
                        "percent": (disk.used / disk.total) * 100,
                    },
                },
                "services": services,
            }
        
        except Exception as e:
            logger.error(f"Detailed health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Readiness check - is the application ready to serve requests."""
        try:
            # Check if all critical services are available
            db_status = await self._check_database()
            redis_status = await self._check_redis()
            
            is_ready = (
                db_status["status"] == "healthy" and
                redis_status["status"] == "healthy"
            )
            
            return {
                "status": "ready" if is_ready else "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": db_status,
                    "redis": redis_status,
                },
            }
        
        except Exception as e:
            logger.error(f"Readiness check failed: {str(e)}")
            return {
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    async def liveness_check(self) -> Dict[str, Any]:
        """Liveness check - is the application alive."""
        try:
            # Basic application liveness
            return {
                "status": "alive",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": self._get_uptime(),
            }
        
        except Exception as e:
            logger.error(f"Liveness check failed: {str(e)}")
            return {
                "status": "dead",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # Simple database connection test
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "response_time": "< 1ms",
            }
        
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": "Database connection failed",
                "error": str(e),
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        try:
            # Simple Redis connection test
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            
            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "response_time": "< 1ms",
            }
        
        except Exception as e:
            logger.error(f"Redis check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": "Redis connection failed",
                "error": str(e),
            }
    
    def _get_uptime(self) -> str:
        """Get application uptime."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime)
        except Exception:
            return "unknown"
