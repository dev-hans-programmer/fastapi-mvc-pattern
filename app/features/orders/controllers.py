"""
Orders controllers.
"""
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
import logging

from app.features.orders.services import OrderService
from app.features.orders.types import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderStatsResponse, OrderItemResponse
)
from app.features.orders.validation import validate_order_create, validate_order_update
from app.core.exceptions import NotFoundException, ValidationException
from app.core.thread_pool import run_in_thread

logger = logging.getLogger(__name__)


class OrderController:
    """Order controller."""
    
    def __init__(self, order_service: OrderService):
        self.order_service = order_service
    
    async def create_order(self, user_id: int, order_data: OrderCreate) -> OrderResponse:
        """Create a new order."""
        try:
            # Validate request
            validate_order_create(order_data)
            
            # Create order
            order = await self.order_service.create_order(user_id, order_data)
            
            logger.info(f"Order created successfully: {order.id}")
            
            return OrderResponse.from_orm(order)
        
        except ValidationException as e:
            logger.error(f"Validation error in create_order: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in create_order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order",
            )
    
    async def get_order(self, order_id: int, user_id: Optional[int] = None) -> OrderResponse:
        """Get order by ID."""
        try:
            order = await self.order_service.get_order_by_id(order_id, user_id)
            
            if not order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            return OrderResponse.from_orm(order)
        
        except NotFoundException as e:
            logger.error(f"Order not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get order",
            )
    
    async def get_orders(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
    ) -> OrderListResponse:
        """Get list of orders."""
        try:
            orders, total = await self.order_service.get_orders(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status_filter=status_filter,
            )
            
            order_responses = [OrderResponse.from_orm(order) for order in orders]
            
            return OrderListResponse(
                orders=order_responses,
                total=total,
                skip=skip,
                limit=limit,
            )
        
        except Exception as e:
            logger.error(f"Error in get_orders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get orders",
            )
    
    async def update_order(self, order_id: int, order_data: OrderUpdate) -> OrderResponse:
        """Update order."""
        try:
            # Validate request
            validate_order_update(order_data)
            
            # Update order
            order = await self.order_service.update_order(order_id, order_data)
            
            if not order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            logger.info(f"Order updated successfully: {order.id}")
            
            return OrderResponse.from_orm(order)
        
        except NotFoundException as e:
            logger.error(f"Order not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except ValidationException as e:
            logger.error(f"Validation error in update_order: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in update_order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order",
            )
    
    async def cancel_order(self, order_id: int, user_id: Optional[int] = None) -> Dict[str, str]:
        """Cancel order."""
        try:
            success = await self.order_service.cancel_order(order_id, user_id)
            
            if not success:
                raise NotFoundException(f"Order with ID {order_id} not found or cannot be cancelled")
            
            logger.info(f"Order cancelled successfully: {order_id}")
            
            return {"message": "Order cancelled successfully"}
        
        except NotFoundException as e:
            logger.error(f"Order not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in cancel_order: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel order",
            )
    
    async def update_order_status(self, order_id: int, new_status: str) -> OrderResponse:
        """Update order status."""
        try:
            order = await self.order_service.update_order_status(order_id, new_status)
            
            if not order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            logger.info(f"Order status updated: {order_id} -> {new_status}")
            
            return OrderResponse.from_orm(order)
        
        except NotFoundException as e:
            logger.error(f"Order not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in update_order_status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update order status",
            )
    
    @run_in_thread
    def get_order_stats(self, order_id: int) -> OrderStatsResponse:
        """Get order statistics (CPU-intensive operation)."""
        try:
            stats = self.order_service.calculate_order_stats(order_id)
            
            if not stats:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            return stats
        
        except NotFoundException as e:
            logger.error(f"Order not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_order_stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get order statistics",
            )
    
    async def get_user_orders(self, user_id: int, skip: int = 0, limit: int = 100) -> OrderListResponse:
        """Get orders for a specific user."""
        try:
            orders, total = await self.order_service.get_user_orders(user_id, skip, limit)
            
            order_responses = [OrderResponse.from_orm(order) for order in orders]
            
            return OrderListResponse(
                orders=order_responses,
                total=total,
                skip=skip,
                limit=limit,
            )
        
        except Exception as e:
            logger.error(f"Error in get_user_orders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user orders",
            )
    
    async def process_order_payment(self, order_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process order payment."""
        try:
            result = await self.order_service.process_order_payment(order_id, payment_data)
            
            if not result:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            logger.info(f"Order payment processed: {order_id}")
            
            return result
        
        except NotFoundException as e:
            logger.error(f"Order not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in process_order_payment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process order payment",
            )
