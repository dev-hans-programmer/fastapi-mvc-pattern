"""
Health check controllers
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime, timezone
from fastapi import Depends
import psutil
import asyncio

from app.core.config import get_settings
from app.core.database import get_database_manager
from app.core.background_tasks import task_manager
from app.core.thread_pool import thread_pool_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class HealthController:
    """
    Health check controller
    """
    
    def __init__(self):
        self.start_time = time.time()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Basic health check
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "FastAPI Backend",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        }
    
    async def readiness_check(self) -> Dict[str, Any]:
        """
        Readiness check
        """
        checks = {}
        overall_status = "ready"
        
        # Check database connection
        try:
            db_manager = get_database_manager()
            db_connected = await db_manager.check_connection()
            checks["database"] = {
                "status": "ready" if db_connected else "not_ready",
                "connected": db_connected,
            }
            if not db_connected:
                overall_status = "not_ready"
        except Exception as e:
            checks["database"] = {
                "status": "not_ready",
                "error": str(e),
            }
            overall_status = "not_ready"
        
        # Check background task system
        try:
            worker_stats = task_manager.get_worker_stats()
            checks["background_tasks"] = {
                "status": "ready" if worker_stats else "not_ready",
                "workers": worker_stats,
            }
        except Exception as e:
            checks["background_tasks"] = {
                "status": "not_ready",
                "error": str(e),
            }
            overall_status = "not_ready"
        
        # Check thread pool
        try:
            thread_stats = thread_pool_manager.get_stats()
            checks["thread_pool"] = {
                "status": "ready" if thread_stats["running"] else "not_ready",
                "stats": thread_stats,
            }
        except Exception as e:
            checks["thread_pool"] = {
                "status": "not_ready",
                "error": str(e),
            }
            overall_status = "not_ready"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
        }
    
    async def liveness_check(self) -> Dict[str, Any]:
        """
        Liveness check
        """
        uptime = time.time() - self.start_time
        
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
        }
    
    async def detailed_health_check(self) -> Dict[str, Any]:
        """
        Detailed health check
        """
        checks = {}
        overall_status = "healthy"
        
        # System metrics
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            checks["system"] = {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
            }
            
            # Check if resources are critically low
            if memory.percent > 90 or cpu_percent > 90:
                checks["system"]["status"] = "warning"
                overall_status = "warning"
                
        except Exception as e:
            checks["system"] = {
                "status": "error",
                "error": str(e),
            }
            overall_status = "unhealthy"
        
        # Database check
        try:
            db_manager = get_database_manager()
            db_connected = await db_manager.check_connection()
            table_names = await db_manager.get_table_names() if db_connected else []
            
            checks["database"] = {
                "status": "healthy" if db_connected else "unhealthy",
                "connected": db_connected,
                "table_count": len(table_names),
            }
            
            if not db_connected:
                overall_status = "unhealthy"
                
        except Exception as e:
            checks["database"] = {
                "status": "error",
                "error": str(e),
            }
            overall_status = "unhealthy"
        
        # Background tasks check
        try:
            active_tasks = task_manager.get_active_tasks()
            worker_stats = task_manager.get_worker_stats()
            
            checks["background_tasks"] = {
                "status": "healthy",
                "active_tasks": active_tasks,
                "worker_stats": worker_stats,
            }
            
        except Exception as e:
            checks["background_tasks"] = {
                "status": "error",
                "error": str(e),
            }
            overall_status = "unhealthy"
        
        # Thread pool check
        try:
            thread_stats = thread_pool_manager.get_stats()
            
            checks["thread_pool"] = {
                "status": "healthy" if thread_stats["running"] else "unhealthy",
                "stats": thread_stats,
            }
            
            if not thread_stats["running"]:
                overall_status = "unhealthy"
                
        except Exception as e:
            checks["thread_pool"] = {
                "status": "error",
                "error": str(e),
            }
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "FastAPI Backend",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "uptime_seconds": time.time() - self.start_time,
            "checks": checks,
        }
    
    async def health_metrics(self) -> Dict[str, Any]:
        """
        Health metrics and statistics
        """
        uptime = time.time() - self.start_time
        
        # System metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        # Application metrics
        thread_stats = thread_pool_manager.get_stats()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "environment": settings.ENVIRONMENT,
            "metrics": {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used / (1024 * 1024),
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_percent": (disk.used / disk.total) * 100,
                    "disk_used_gb": disk.used / (1024 * 1024 * 1024),
                    "disk_free_gb": disk.free / (1024 * 1024 * 1024),
                },
                "application": {
                    "thread_pool": thread_stats,
                    "active_tasks": thread_stats.get("active_tasks", 0),
                    "completed_tasks": thread_stats.get("completed_tasks", 0),
                    "failed_tasks": thread_stats.get("failed_tasks", 0),
                },
            },
        }
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """
        Format uptime in human-readable format
        """
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)
