"""
Main API router for version 1.
"""
from fastapi import APIRouter

from app.features.auth.routes import router as auth_router
from app.features.users.routes import router as users_router
from app.features.products.routes import router as products_router
from app.features.orders.routes import router as orders_router
from app.features.health.routes import router as health_router

api_router = APIRouter()

# Include feature routers
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
