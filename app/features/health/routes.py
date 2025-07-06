"""
Health check routes.
"""
from fastapi import APIRouter, Depends
from app.features.health.controllers import HealthController

router = APIRouter()


def get_health_controller() -> HealthController:
    """Get health controller."""
    return HealthController()


@router.get("/")
async def health_check(
    health_controller: HealthController = Depends(get_health_controller),
):
    """Basic health check."""
    return await health_controller.health_check()


@router.get("/detailed")
async def detailed_health_check(
    health_controller: HealthController = Depends(get_health_controller),
):
    """Detailed health check."""
    return await health_controller.detailed_health_check()


@router.get("/readiness")
async def readiness_check(
    health_controller: HealthController = Depends(get_health_controller),
):
    """Readiness check."""
    return await health_controller.readiness_check()


@router.get("/liveness")
async def liveness_check(
    health_controller: HealthController = Depends(get_health_controller),
):
    """Liveness check."""
    return await health_controller.liveness_check()
