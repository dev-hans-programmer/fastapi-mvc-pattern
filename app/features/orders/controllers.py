"""
Order controllers
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import NotFoundError, ValidationError, BusinessLogicError
from app.features.orders.services import OrderService
from app.features.orders.repositories import OrderRepository
from app.features.orders.types import OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate
from app.features.products.repositories import ProductRepository
from app.features.users.types import User
from app.common.responses import success_response, paginated_response, list_response
from app.common.decorators import timer, log_execution
from app.core.dependencies import CommonQueryParams

logger = logging.getLogger(__name__)


class OrderController:
    """Order controller"""
    
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session
        self.order_repository = OrderRepository(session)
        self.product_repository = ProductRepository(session)
        self.order_service = OrderService(self.order_repository, self.product_repository)
    
    @timer
    @log_execution()
    async def create_order(self, order_data: OrderCreate, current_user: User) -> Dict[str, Any]:
        """Create a new order"""
        try:
            # Set user_id from current user
            order_dict = order_data.dict()
            order_dict["user_id"] = current_user.id
            
            order = await self.order_service.create_order(order_dict)
            
            return success_response(
                data=OrderResponse.from_orm(order).dict(),
                message="Order created successfully"
            )
            
        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_order(self, order_id: int, current_user: User) -> Dict[str, Any]:
        """Get order by ID"""
        try:
            order = await self.order_service.get_by_id(order_id)
            
            if not order:
                raise NotFoundError(f"Order with ID {order_id} not found")
            
            # Check if user can access this order
            if order.user_id != current_user.id and getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this order"
                )
            
            return success_response(
                data=OrderResponse.from_orm(order).dict(),
                message="Order retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get order failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_orders(self, params: CommonQueryParams, current_user: User) -> Dict[str, Any]:
        """Get orders for current user"""
        try:
            # Users can only see their own orders unless they're admin
            filters = {}
            if getattr(current_user, 'role', 'user') != 'admin':
                filters["user_id"] = current_user.id
            
            orders = await self.order_service.get_all(
                skip=params.skip,
                limit=params.limit,
                filters=filters,
                order_by=params.sort_by or "created_at",
                order_desc=params.sort_order == "desc"
            )
            
            order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
            
            return list_response(
                data=order_responses,
                message="Orders retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get orders failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_orders_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        current_user: User = None
    ) -> Dict[str, Any]:
        """Get orders with pagination"""
        try:
            filters = {}
            if getattr(current_user, 'role', 'user') != 'admin':
                filters["user_id"] = current_user.id
            
            if status:
                filters["status"] = status
            
            result = await self.order_service.get_paginated(
                page=page,
                page_size=page_size,
                filters=filters,
                order_by="created_at",
                order_desc=True
            )
            
            order_responses = [OrderResponse.from_orm(order).dict() for order in result['records']]
            
            return {
                "success": True,
                "message": "Orders retrieved successfully",
                "data": order_responses,
                "pagination": result['pagination']
            }
            
        except Exception as e:
            logger.error(f"Get paginated orders failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def update_order(self, order_id: int, order_data: OrderUpdate, current_user: User) -> Dict[str, Any]:
        """Update order"""
        try:
            order = await self.order_service.get_by_id(order_id)
            
            if not order:
                raise NotFoundError(f"Order with ID {order_id} not found")
            
            # Check permissions
            if order.user_id != current_user.id and getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this order"
                )
            
            updated_order = await self.order_service.update(order_id, order_data)
            
            return success_response(
                data=OrderResponse.from_orm(updated_order).dict(),
                message="Order updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Order update failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def cancel_order(self, order_id: int, current_user: User) -> Dict[str, Any]:
        """Cancel order"""
        try:
            order = await self.order_service.get_by_id(order_id)
            
            if not order:
                raise NotFoundError(f"Order with ID {order_id} not found")
            
            # Check permissions
            if order.user_id != current_user.id and getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to cancel this order"
                )
            
            cancelled_order = await self.order_service.cancel_order(order_id)
            
            return success_response(
                data=OrderResponse.from_orm(cancelled_order).dict(),
                message="Order cancelled successfully"
            )
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def update_order_status(self, order_id: int, status: str, current_user: User) -> Dict[str, Any]:
        """Update order status (Admin only)"""
        try:
            if getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can update order status"
                )
            
            order = await self.order_service.update_order_status(order_id, status)
            
            return success_response(
                data=OrderResponse.from_orm(order).dict(),
                message=f"Order status updated to {status}"
            )
            
        except Exception as e:
            logger.error(f"Order status update failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_order_statistics(self, current_user: User) -> Dict[str, Any]:
        """Get order statistics"""
        try:
            if getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can view order statistics"
                )
            
            stats = await self.order_service.get_order_statistics()
            
            return success_response(
                data=stats,
                message="Order statistics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get order statistics failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_user_order_history(self, current_user: User) -> Dict[str, Any]:
        """Get user's order history"""
        try:
            orders = await self.order_service.get_user_order_history(current_user.id)
            
            order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
            
            return list_response(
                data=order_responses,
                message="Order history retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get user order history failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_orders_by_status(self, status: str, current_user: User) -> Dict[str, Any]:
        """Get orders by status"""
        try:
            if getattr(current_user, 'role', 'user') != 'admin':
                # Users can only see their own orders
                orders = await self.order_service.get_user_orders_by_status(current_user.id, status)
            else:
                orders = await self.order_service.get_orders_by_status(status)
            
            order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
            
            return list_response(
                data=order_responses,
                message=f"Orders with status '{status}' retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get orders by status failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def add_order_item(self, order_id: int, item_data: OrderItemCreate, current_user: User) -> Dict[str, Any]:
        """Add item to order"""
        try:
            order = await self.order_service.get_by_id(order_id)
            
            if not order:
                raise NotFoundError(f"Order with ID {order_id} not found")
            
            # Check permissions
            if order.user_id != current_user.id and getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to modify this order"
                )
            
            # Check if order can be modified
            if order.status not in ['pending', 'confirmed']:
                raise BusinessLogicError("Cannot add items to order in current status")
            
            updated_order = await self.order_service.add_order_item(order_id, item_data.dict())
            
            return success_response(
                data=OrderResponse.from_orm(updated_order).dict(),
                message="Item added to order successfully"
            )
            
        except Exception as e:
            logger.error(f"Add order item failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def remove_order_item(self, order_id: int, item_id: int, current_user: User) -> Dict[str, Any]:
        """Remove item from order"""
        try:
            order = await self.order_service.get_by_id(order_id)
            
            if not order:
                raise NotFoundError(f"Order with ID {order_id} not found")
            
            # Check permissions
            if order.user_id != current_user.id and getattr(current_user, 'role', 'user') != 'admin':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to modify this order"
                )
            
            # Check if order can be modified
            if order.status not in ['pending', 'confirmed']:
                raise BusinessLogicError("Cannot remove items from order in current status")
            
            updated_order = await self.order_service.remove_order_item(order_id, item_id)
            
            return success_response(
                data=OrderResponse.from_orm(updated_order).dict(),
                message="Item removed from order successfully"
            )
            
        except Exception as e:
            logger.error(f"Remove order item failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def calculate_order_total(self, order_data: OrderCreate) -> Dict[str, Any]:
        """Calculate order total before creating"""
        try:
            total_info = await self.order_service.calculate_order_total(order_data.dict())
            
            return success_response(
                data=total_info,
                message="Order total calculated successfully"
            )
            
        except Exception as e:
            logger.error(f"Calculate order total failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_recent_orders(self, days: int = 30, current_user: User = None) -> Dict[str, Any]:
        """Get recent orders"""
        try:
            if getattr(current_user, 'role', 'user') != 'admin':
                orders = await self.order_service.get_user_recent_orders(current_user.id, days)
            else:
                orders = await self.order_service.get_recent_orders(days)
            
            order_responses = [OrderResponse.from_orm(order).dict() for order in orders]
            
            return list_response(
                data=order_responses,
                message=f"Orders from last {days} days retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get recent orders failed: {e}")
            raise
