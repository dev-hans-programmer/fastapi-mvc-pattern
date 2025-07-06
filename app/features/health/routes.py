"""
Health check routes
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.features.health.controllers import HealthController

router = APIRouter()


@router.get("/")
async def health_check(
    controller: HealthController = Depends(),
):
    """
    Basic health check
    """
    return await controller.health_check()


@router.get("/ready")
async def readiness_check(
    controller: HealthController = Depends(),
):
    """
    Readiness check - indicates if the application is ready to serve traffic
    """
    return await controller.readiness_check()


@router.get("/live")
async def liveness_check(
    controller: HealthController = Depends(),
):
    """
    Liveness check - indicates if the application is alive
    """
    return await controller.liveness_check()


@router.get("/detailed")
async def detailed_health_check(
    controller: HealthController = Depends(),
):
    """
    Detailed health check with component status
    """
    return await controller.detailed_health_check()


@router.get("/metrics")
async def health_metrics(
    controller: HealthController = Depends(),
):
    """
    Health metrics and statistics
    """
    return await controller.health_metrics()


# Export router
health_router = router
