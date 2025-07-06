"""
Orders services.
"""
from typing import List, Optional, Tuple, Dict, Any
import logging
from datetime import datetime

from app.features.orders.repositories import OrderRepository
from app.features.orders.types import OrderCreate, OrderUpdate, OrderStatsResponse
from app.features.users.repositories import UserRepository
from app.features.products.repositories import ProductRepository
from app.models.order import Order
from app.core.exceptions import NotFoundException, ValidationException, BusinessLogicException
from app.core.thread_pool import AsyncBatchProcessor
from app.tasks.order_tasks import send_order_confirmation, process_order_fulfillment

logger = logging.getLogger(__name__)


class OrderService:
    """Order service."""
    
    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
    ):
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.product_repository = product_repository
    
    async def create_order(self, user_id: int, order_data: OrderCreate) -> Order:
        """Create a new order."""
        try:
            # Validate user exists
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise NotFoundException("User not found")
            
            # Validate products and calculate total
            total_amount = 0.0
            order_items = []
            
            for item in order_data.items:
                product = await self.product_repository.get_by_id(item.product_id)
                if not product:
                    raise ValidationException(f"Product {item.product_id} not found")
                
                if not product.is_active:
                    raise ValidationException(f"Product {product.name} is not available")
                
                if product.inventory_count < item.quantity:
                    raise ValidationException(f"Insufficient inventory for product {product.name}")
                
                item_total = float(product.price) * item.quantity
                total_amount += item_total
                
                order_items.append({
                    "product_id": product.id,
                    "quantity": item.quantity,
                    "unit_price": float(product.price),
                    "total_price": item_total,
                })
            
            # Create order
            order_dict = {
                "user_id": user_id,
                "status": "pending",
                "total_amount": total_amount,
                "shipping_address": order_data.shipping_address,
                "notes": order_data.notes,
            }
            
            order = await self.order_repository.create(order_dict, order_items)
            
            # Update product inventory
            for item in order_data.items:
                product = await self.product_repository.get_by_id(item.product_id)
                new_inventory = product.inventory_count - item.quantity
                await self.product_repository.update_inventory(item.product_id, new_inventory)
            
            # Send confirmation email (background task)
            send_order_confirmation.delay(order.id, user.email)
            
            logger.info(f"Order created: {order.id}")
            return order
        
        except Exception as e:
            logger.error(f"Error in create_order: {str(e)}")
            raise
    
    async def get_order_by_id(self, order_id: int, user_id: Optional[int] = None) -> Optional[Order]:
        """Get order by ID."""
        try:
            order = await self.order_repository.get_by_id(order_id)
            
            # Check if user has access to this order
            if user_id and order and order.user_id != user_id:
                return None
            
            return order
        except Exception as e:
            logger.error(f"Error in get_order_by_id: {str(e)}")
            raise
    
    async def get_orders(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """Get list of orders with pagination and filtering."""
        try:
            return await self.order_repository.get_multi(
                user_id=user_id,
                skip=skip,
                limit=limit,
                status_filter=status_filter,
            )
        except Exception as e:
            logger.error(f"Error in get_orders: {str(e)}")
            raise
    
    async def update_order(self, order_id: int, order_data: OrderUpdate) -> Optional[Order]:
        """Update order."""
        try:
            # Get existing order
            existing_order = await self.order_repository.get_by_id(order_id)
            if not existing_order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            # Check if order can be updated
            if existing_order.status in ["shipped", "delivered", "cancelled"]:
                raise BusinessLogicException("Cannot update order in current status")
            
            # Update order
            update_data = order_data.dict(exclude_unset=True)
            order = await self.order_repository.update(order_id, update_data)
            
            logger.info(f"Order updated: {order.id if order else order_id}")
            return order
        
        except Exception as e:
            logger.error(f"Error in update_order: {str(e)}")
            raise
    
    async def cancel_order(self, order_id: int, user_id: Optional[int] = None) -> bool:
        """Cancel order."""
        try:
            # Get existing order
            existing_order = await self.order_repository.get_by_id(order_id)
            if not existing_order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            # Check user access
            if user_id and existing_order.user_id != user_id:
                raise NotFoundException("Order not found")
            
            # Check if order can be cancelled
            if existing_order.status in ["shipped", "delivered", "cancelled"]:
                raise BusinessLogicException("Cannot cancel order in current status")
            
            # Cancel order
            result = await self.order_repository.update(order_id, {"status": "cancelled"})
            
            # Restore product inventory
            order_items = await self.order_repository.get_order_items(order_id)
            for item in order_items:
                product = await self.product_repository.get_by_id(item.product_id)
                if product:
                    new_inventory = product.inventory_count + item.quantity
                    await self.product_repository.update_inventory(item.product_id, new_inventory)
            
            logger.info(f"Order cancelled: {order_id}")
            return result is not None
        
        except Exception as e:
            logger.error(f"Error in cancel_order: {str(e)}")
            raise
    
    async def update_order_status(self, order_id: int, new_status: str) -> Optional[Order]:
        """Update order status."""
        try:
            # Validate status
            valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
            if new_status not in valid_statuses:
                raise ValidationException(f"Invalid status: {new_status}")
            
            # Get existing order
            existing_order = await self.order_repository.get_by_id(order_id)
            if not existing_order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            # Update status
            order = await self.order_repository.update(order_id, {"status": new_status})
            
            # Process fulfillment if order is confirmed
            if new_status == "confirmed":
                process_order_fulfillment.delay(order_id)
            
            logger.info(f"Order status updated: {order_id} -> {new_status}")
            return order
        
        except Exception as e:
            logger.error(f"Error in update_order_status: {str(e)}")
            raise
    
    def calculate_order_stats(self, order_id: int) -> Optional[OrderStatsResponse]:
        """Calculate order statistics (CPU-intensive operation)."""
        try:
            # This is a CPU-intensive operation that should run in thread pool
            order = self.order_repository.get_by_id_sync(order_id)
            if not order:
                return None
            
            # Simulate heavy computation
            import time
            time.sleep(0.1)  # Simulate processing time
            
            stats_data = self.order_repository.calculate_order_stats_sync(order_id)
            
            return OrderStatsResponse(
                order_id=order_id,
                total_amount=stats_data.get("total_amount", 0.0),
                item_count=stats_data.get("item_count", 0),
                processing_time=stats_data.get("processing_time", 0),
                shipping_cost=stats_data.get("shipping_cost", 0.0),
                tax_amount=stats_data.get("tax_amount", 0.0),
                discount_amount=stats_data.get("discount_amount", 0.0),
            )
        
        except Exception as e:
            logger.error(f"Error in calculate_order_stats: {str(e)}")
            raise
    
    async def get_user_orders(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Order], int]:
        """Get orders for a specific user."""
        try:
            return await self.order_repository.get_user_orders(user_id, skip, limit)
        except Exception as e:
            logger.error(f"Error in get_user_orders: {str(e)}")
            raise
    
    async def process_order_payment(self, order_id: int, payment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process order payment."""
        try:
            # Get existing order
            existing_order = await self.order_repository.get_by_id(order_id)
            if not existing_order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            # Check if order can be paid
            if existing_order.status not in ["pending", "confirmed"]:
                raise BusinessLogicException("Cannot process payment for order in current status")
            
            # Process payment (mock implementation)
            payment_result = {
                "payment_id": f"pay_{order_id}_{datetime.utcnow().timestamp()}",
                "status": "completed",
                "amount": existing_order.total_amount,
                "method": payment_data.get("method", "credit_card"),
                "processed_at": datetime.utcnow().isoformat(),
            }
            
            # Update order status
            await self.order_repository.update(order_id, {"status": "confirmed"})
            
            logger.info(f"Order payment processed: {order_id}")
            return payment_result
        
        except Exception as e:
            logger.error(f"Error in process_order_payment: {str(e)}")
            raise
    
    async def get_order_summary(self, user_id: int) -> Dict[str, Any]:
        """Get order summary for user."""
        try:
            summary = await self.order_repository.get_user_order_summary(user_id)
            return summary
        except Exception as e:
            logger.error(f"Error in get_order_summary: {str(e)}")
            raise
