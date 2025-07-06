"""
Order routes
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user, get_current_active_user, get_current_admin_user, CommonQueryParams
from app.features.orders.controllers import OrderController
from app.features.orders.types import OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
from app.features.users.types import User
from app.common.decorators import rate_limit
from app.common.responses import success_response

logger = logging.getLogger(__name__)

orders_router = APIRouter()


@orders_router.post("/", response_model=Dict[str, Any])
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new order"""
    controller = OrderController(session)
    return await controller.create_order(order_data, current_user)


@orders_router.get("/{order_id}", response_model=Dict[str, Any])
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get order by ID"""
    controller = OrderController(session)
    return await controller.get_order(order_id, current_user)


@orders_router.get("/", response_model=Dict[str, Any])
async def get_orders(
    params: CommonQueryParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get orders for current user"""
    controller = OrderController(session)
    return await controller.get_orders(params, current_user)


@orders_router.get("/paginated/list", response_model=Dict[str, Any])
async def get_orders_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get orders with pagination"""
    controller = OrderController(session)
    return await controller.get_orders_paginated(page, page_size, status, current_user)


@orders_router.put("/{order_id}", response_model=Dict[str, Any])
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Update order"""
    controller = OrderController(session)
    return await controller.update_order(order_id, order_data, current_user)


@orders_router.patch("/{order_id}/cancel", response_model=Dict[str, Any])
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Cancel order"""
    controller = OrderController(session)
    return await controller.cancel_order(order_id, current_user)


@orders_router.patch("/{order_id}/status", response_model=Dict[str, Any])
async def update_order_status(
    order_id: int,
    status: str = Query(..., description="New order status"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Update order status (Admin only)"""
    controller = OrderController(session)
    return await controller.update_order_status(order_id, status, current_user)


@orders_router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_order_statistics(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get order statistics (Admin only)"""
    controller = OrderController(session)
    return await controller.get_order_statistics(current_user)


@orders_router.get("/history/my", response_model=Dict[str, Any])
async def get_my_order_history(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get current user's order history"""
    controller = OrderController(session)
    return await controller.get_user_order_history(current_user)


@orders_router.get("/status/{status}", response_model=Dict[str, Any])
async def get_orders_by_status(
    status: str,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get orders by status"""
    controller = OrderController(session)
    return await controller.get_orders_by_status(status, current_user)


@orders_router.post("/{order_id}/items", response_model=Dict[str, Any])
async def add_order_item(
    order_id: int,
    item_data: OrderItemCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Add item to order"""
    controller = OrderController(session)
    return await controller.add_order_item(order_id, item_data, current_user)


@orders_router.delete("/{order_id}/items/{item_id}", response_model=Dict[str, Any])
async def remove_order_item(
    order_id: int,
    item_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Remove item from order"""
    controller = OrderController(session)
    return await controller.remove_order_item(order_id, item_id, current_user)


@orders_router.post("/calculate-total", response_model=Dict[str, Any])
async def calculate_order_total(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Calculate order total before creating"""
    controller = OrderController(session)
    return await controller.calculate_order_total(order_data)


@orders_router.get("/recent/list", response_model=Dict[str, Any])
async def get_recent_orders(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Get recent orders"""
    controller = OrderController(session)
    return await controller.get_recent_orders(days, current_user)


@orders_router.get("/admin/all", response_model=Dict[str, Any])
async def get_all_orders_admin(
    params: CommonQueryParams = Depends(),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get all orders (Admin only)"""
    # Remove user filter for admin
    from app.features.orders.services import OrderService
    from app.features.orders.repositories import OrderRepository
    from app.features.products.repositories import ProductRepository
    
    order_repository = OrderRepository(session)
    product_repository = ProductRepository(session)
    order_service = OrderService(order_repository, product_repository)
    
    orders = await order_service.get_all(
        skip=params.skip,
        limit=params.limit,
        order_by=params.sort_by or "created_at",
        order_desc=params.sort_order == "desc"
    )
    
    from app.features.orders.types import OrderResponse
    order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
    
    return success_response(
        data=order_responses,
        message="All orders retrieved successfully"
    )


@orders_router.get("/admin/pending", response_model=Dict[str, Any])
async def get_pending_orders_admin(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get pending orders (Admin only)"""
    from app.features.orders.repositories import OrderRepository
    
    order_repository = OrderRepository(session)
    orders = await order_repository.get_pending_orders()
    
    from app.features.orders.types import OrderResponse
    order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
    
    return success_response(
        data=order_responses,
        message="Pending orders retrieved successfully"
    )


@orders_router.get("/admin/needs-shipment", response_model=Dict[str, Any])
async def get_orders_needing_shipment(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get orders that need shipment (Admin only)"""
    from app.features.orders.repositories import OrderRepository
    
    order_repository = OrderRepository(session)
    orders = await order_repository.get_orders_needing_shipment()
    
    from app.features.orders.types import OrderResponse
    order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
    
    return success_response(
        data=order_responses,
        message="Orders needing shipment retrieved successfully"
    )


@orders_router.get("/search/query", response_model=Dict[str, Any])
async def search_orders(
    search_term: str = Query(..., min_length=2, description="Search term"),
    skip: int = Query(0, ge=0, description="Skip items"),
    limit: int = Query(20, ge=1, le=100, description="Limit items"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session)
):
    """Search orders"""
    from app.features.orders.repositories import OrderRepository
    
    order_repository = OrderRepository(session)
    
    # Users can only search their own orders unless they're admin
    user_id = None if getattr(current_user, 'role', 'user') == 'admin' else current_user.id
    
    orders = await order_repository.search_orders(search_term, user_id, skip, limit)
    
    from app.features.orders.types import OrderResponse
    order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
    
    return success_response(
        data=order_responses,
        message="Order search completed"
    )


@orders_router.get("/analytics/top-customers", response_model=Dict[str, Any])
async def get_top_customers(
    limit: int = Query(10, ge=1, le=100, description="Number of top customers"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get top customers by order value (Admin only)"""
    from app.features.orders.repositories import OrderRepository
    
    order_repository = OrderRepository(session)
    top_customers = await order_repository.get_top_customers(limit)
    
    return success_response(
        data=top_customers,
        message="Top customers retrieved successfully"
    )


@orders_router.get("/analytics/revenue", response_model=Dict[str, Any])
async def get_revenue_analytics(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get revenue analytics (Admin only)"""
    from app.features.orders.repositories import OrderRepository
    
    order_repository = OrderRepository(session)
    revenue_stats = await order_repository.get_revenue_statistics()
    
    return success_response(
        data=revenue_stats,
        message="Revenue analytics retrieved successfully"
    )
