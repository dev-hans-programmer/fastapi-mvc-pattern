"""
Order routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Dict, Any

from app.features.orders.controllers import OrderController
from app.features.orders.validation import (
    OrderCreateRequest,
    OrderUpdateRequest,
    OrderResponse,
    OrderListResponse,
    OrderItemResponse,
)
from app.core.dependencies import (
    get_current_user,
    get_admin_user,
    get_pagination_params,
    get_sorting_params,
    get_filtering_params,
)

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: OrderController = Depends(),
):
    """
    Create a new order
    """
    try:
        order = await controller.create_order(request, current_user["id"])
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    current_user: Dict[str, Any] = Depends(get_current_user),
    pagination: Dict[str, Any] = Depends(get_pagination_params),
    sorting: Dict[str, Any] = Depends(get_sorting_params),
    filters: Dict[str, Any] = Depends(get_filtering_params),
    controller: OrderController = Depends(),
):
    """
    Get list of orders
    """
    try:
        # Non-admin users can only see their own orders
        if current_user["role"] != "admin":
            filters["user_id"] = current_user["id"]
        
        orders = await controller.list_orders(
            skip=pagination["offset"],
            limit=pagination["limit"],
            sort_by=sorting["sort_by"],
            sort_order=sorting["sort_order"],
            filters=filters,
        )
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my-orders", response_model=OrderListResponse)
async def get_my_orders(
    current_user: Dict[str, Any] = Depends(get_current_user),
    pagination: Dict[str, Any] = Depends(get_pagination_params),
    sorting: Dict[str, Any] = Depends(get_sorting_params),
    controller: OrderController = Depends(),
):
    """
    Get current user's orders
    """
    try:
        orders = await controller.get_user_orders(
            user_id=current_user["id"],
            skip=pagination["offset"],
            limit=pagination["limit"],
            sort_by=sorting["sort_by"],
            sort_order=sorting["sort_order"],
        )
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: OrderController = Depends(),
):
    """
    Get order by ID
    """
    try:
        order = await controller.get_order(order_id, current_user["id"], current_user["role"])
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    request: OrderUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: OrderController = Depends(),
):
    """
    Update order by ID
    """
    try:
        order = await controller.update_order(order_id, request, current_user["id"], current_user["role"])
        return order
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: OrderController = Depends(),
):
    """
    Cancel order by ID
    """
    try:
        await controller.cancel_order(order_id, current_user["id"], current_user["role"])
        return {"message": "Order cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    controller: OrderController = Depends(),
):
    """
    Confirm order (Admin only)
    """
    try:
        await controller.confirm_order(order_id)
        return {"message": "Order confirmed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/ship")
async def ship_order(
    order_id: str,
    tracking_number: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_admin_user),
    controller: OrderController = Depends(),
):
    """
    Ship order (Admin only)
    """
    try:
        await controller.ship_order(order_id, tracking_number)
        return {"message": "Order shipped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/deliver")
async def deliver_order(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    controller: OrderController = Depends(),
):
    """
    Mark order as delivered (Admin only)
    """
    try:
        await controller.deliver_order(order_id)
        return {"message": "Order marked as delivered successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
async def get_order_items(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: OrderController = Depends(),
):
    """
    Get order items
    """
    try:
        items = await controller.get_order_items(order_id, current_user["id"], current_user["role"])
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}/status-history")
async def get_order_status_history(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    controller: OrderController = Depends(),
):
    """
    Get order status history
    """
    try:
        history = await controller.get_order_status_history(order_id, current_user["id"], current_user["role"])
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}/stats")
async def get_order_stats(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    controller: OrderController = Depends(),
):
    """
    Get order statistics (Admin only)
    """
    try:
        stats = await controller.get_order_stats(order_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats/summary")
async def get_orders_summary(
    current_user: Dict[str, Any] = Depends(get_admin_user),
    controller: OrderController = Depends(),
):
    """
    Get orders summary statistics (Admin only)
    """
    try:
        summary = await controller.get_orders_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/bulk-update-status")
async def bulk_update_order_status(
    order_ids: List[str],
    status: str,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    controller: OrderController = Depends(),
):
    """
    Bulk update order status (Admin only)
    """
    try:
        result = await controller.bulk_update_order_status(order_ids, status)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Export router
orders_router = router
