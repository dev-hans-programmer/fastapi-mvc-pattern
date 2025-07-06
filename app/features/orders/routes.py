"""
Orders routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any

from app.features.orders.controllers import OrderController
from app.features.orders.services import OrderService
from app.features.orders.repositories import OrderRepository
from app.features.orders.types import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse, OrderStatsResponse
)
from app.features.users.repositories import UserRepository
from app.features.products.repositories import ProductRepository
from app.core.dependencies import get_db, get_current_user_id
from app.core.database import Session

router = APIRouter()


def get_order_controller(db: Session = Depends(get_db)) -> OrderController:
    """Get order controller."""
    order_repository = OrderRepository(db)
    user_repository = UserRepository(db)
    product_repository = ProductRepository(db)
    order_service = OrderService(order_repository, user_repository, product_repository)
    return OrderController(order_service)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Create a new order."""
    return await order_controller.create_order(current_user_id, order_data)


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to return"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Get list of orders (admin only)."""
    return await order_controller.get_orders(
        skip=skip,
        limit=limit,
        status_filter=status,
    )


@router.get("/me", response_model=OrderListResponse)
async def get_my_orders(
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to return"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Get current user's orders."""
    return await order_controller.get_orders(
        user_id=current_user_id,
        skip=skip,
        limit=limit,
        status_filter=status,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Get order by ID."""
    return await order_controller.get_order(order_id, current_user_id)


@router.get("/{order_id}/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Get order statistics."""
    return await order_controller.get_order_stats(order_id)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Update order."""
    return await order_controller.update_order(order_id, order_data)


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: int,
    new_status: str,
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Update order status."""
    return await order_controller.update_order_status(order_id, new_status)


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Cancel order."""
    return await order_controller.cancel_order(order_id, current_user_id)


@router.post("/{order_id}/payment")
async def process_order_payment(
    order_id: int,
    payment_data: Dict[str, Any],
    current_user_id: int = Depends(get_current_user_id),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Process order payment."""
    return await order_controller.process_order_payment(order_id, payment_data)


@router.get("/users/{user_id}/orders", response_model=OrderListResponse)
async def get_user_orders(
    user_id: int,
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to return"),
    order_controller: OrderController = Depends(get_order_controller),
):
    """Get orders for a specific user (admin only)."""
    return await order_controller.get_user_orders(user_id, skip, limit)
