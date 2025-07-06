"""
Order services
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.exceptions import NotFoundError, ValidationError, BusinessLogicError
from app.features.orders.repositories import OrderRepository
from app.features.orders.types import Order, OrderCreate, OrderUpdate, OrderItem
from app.features.products.repositories import ProductRepository
from app.common.base_service import BaseService
from app.common.validators import BaseValidator

logger = logging.getLogger(__name__)


class OrderService(BaseService[Order, OrderCreate, OrderUpdate]):
    """Order service"""
    
    def __init__(self, order_repository: OrderRepository, product_repository: ProductRepository):
        super().__init__(order_repository)
        self.order_repository = order_repository
        self.product_repository = product_repository
    
    async def _validate_create(self, obj_in: OrderCreate) -> None:
        """Validate order creation"""
        # Validate order items
        if not obj_in.items or len(obj_in.items) == 0:
            raise ValidationError("Order must contain at least one item")
        
        # Validate each item
        for item in obj_in.items:
            # Check if product exists
            product = await self.product_repository.get_by_id(item.product_id)
            if not product:
                raise NotFoundError(f"Product with ID {item.product_id} not found")
            
            # Check if product is available
            if not product.is_available:
                raise BusinessLogicError(f"Product '{product.name}' is not available")
            
            # Check stock availability
            if product.stock_quantity < item.quantity:
                raise BusinessLogicError(f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, Requested: {item.quantity}")
            
            # Validate quantity
            if item.quantity <= 0:
                raise ValidationError(f"Quantity must be greater than 0 for product '{product.name}'")
    
    async def _validate_update(self, db_obj: Order, obj_in: OrderUpdate) -> None:
        """Validate order update"""
        # Check if order can be updated based on status
        if db_obj.status in ['shipped', 'delivered', 'cancelled']:
            raise BusinessLogicError("Cannot update order in current status")
    
    async def _pre_create(self, obj_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-create processing"""
        # Calculate totals
        total_info = await self.calculate_order_total(obj_data)
        
        obj_data.update({
            "subtotal": total_info["subtotal"],
            "tax_amount": total_info["tax_amount"],
            "shipping_cost": total_info["shipping_cost"],
            "total_amount": total_info["total_amount"],
            "status": "pending",
            "order_number": await self._generate_order_number()
        })
        
        return obj_data
    
    async def _post_create(self, db_obj: Order) -> None:
        """Post-create processing"""
        # Reserve stock for order items
        await self._reserve_stock(db_obj.id)
        
        # Send order confirmation (in a real app)
        logger.info(f"Order {db_obj.order_number} created successfully")
    
    async def _generate_order_number(self) -> str:
        """Generate unique order number"""
        import secrets
        from datetime import datetime
        
        date_part = datetime.utcnow().strftime("%Y%m%d")
        random_part = secrets.token_hex(4).upper()
        
        return f"ORD-{date_part}-{random_part}"
    
    async def calculate_order_total(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate order totals"""
        subtotal = Decimal('0.00')
        tax_amount = Decimal('0.00')
        
        for item_data in order_data.get('items', []):
            product = await self.product_repository.get_by_id(item_data['product_id'])
            if not product:
                raise NotFoundError(f"Product with ID {item_data['product_id']} not found")
            
            item_total = Decimal(str(product.price)) * item_data['quantity']
            subtotal += item_total
            
            # Calculate tax if applicable
            if product.tax_rate:
                tax_amount += item_total * Decimal(str(product.tax_rate))
        
        # Calculate shipping cost
        shipping_cost = await self._calculate_shipping_cost(order_data)
        
        total_amount = subtotal + tax_amount + shipping_cost
        
        return {
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "shipping_cost": float(shipping_cost),
            "total_amount": float(total_amount)
        }
    
    async def _calculate_shipping_cost(self, order_data: Dict[str, Any]) -> Decimal:
        """Calculate shipping cost"""
        # Simple shipping calculation - in a real app this would be more complex
        shipping_address = order_data.get('shipping_address', {})
        
        if not shipping_address:
            return Decimal('0.00')
        
        # Free shipping for orders over $100
        subtotal = Decimal('0.00')
        for item_data in order_data.get('items', []):
            product = await self.product_repository.get_by_id(item_data['product_id'])
            if product:
                subtotal += Decimal(str(product.price)) * item_data['quantity']
        
        if subtotal >= Decimal('100.00'):
            return Decimal('0.00')
        
        # Standard shipping cost
        return Decimal('9.99')
    
    async def create_order(self, order_data: Dict[str, Any]) -> Order:
        """Create a new order"""
        try:
            # Create order
            order = await self.create(order_data)
            
            # Create order items
            for item_data in order_data.get('items', []):
                await self.order_repository.create_order_item(order.id, item_data)
            
            # Return order with items
            return await self.order_repository.get_order_with_items(order.id)
            
        except Exception as e:
            logger.error(f"Order creation failed: {e}")
            raise
    
    async def update_order_status(self, order_id: int, new_status: str) -> Order:
        """Update order status"""
        try:
            order = await self.get_by_id_or_raise(order_id)
            
            # Validate status transition
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': [],
                'cancelled': []
            }
            
            if new_status not in valid_transitions.get(order.status, []):
                raise BusinessLogicError(f"Cannot change status from {order.status} to {new_status}")
            
            # Update status
            updated_order = await self.update(order_id, {"status": new_status})
            
            # Handle status-specific logic
            await self._handle_status_change(order, new_status)
            
            logger.info(f"Order {order.order_number} status changed to {new_status}")
            return updated_order
            
        except Exception as e:
            logger.error(f"Order status update failed: {e}")
            raise
    
    async def _handle_status_change(self, order: Order, new_status: str) -> None:
        """Handle status-specific logic"""
        if new_status == 'confirmed':
            # Confirm stock reservation
            await self._confirm_stock_reservation(order.id)
        elif new_status == 'cancelled':
            # Release reserved stock
            await self._release_stock(order.id)
        elif new_status == 'shipped':
            # Send shipping notification (in a real app)
            logger.info(f"Shipping notification sent for order {order.order_number}")
        elif new_status == 'delivered':
            # Mark as delivered, update delivery date
            await self.update(order.id, {"delivered_at": datetime.utcnow()})
    
    async def cancel_order(self, order_id: int) -> Order:
        """Cancel an order"""
        try:
            order = await self.get_by_id_or_raise(order_id)
            
            if order.status in ['delivered', 'cancelled']:
                raise BusinessLogicError("Cannot cancel order in current status")
            
            cancelled_order = await self.update_order_status(order_id, 'cancelled')
            
            logger.info(f"Order {order.order_number} cancelled")
            return cancelled_order
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            raise
    
    async def _reserve_stock(self, order_id: int) -> None:
        """Reserve stock for order items"""
        try:
            order_items = await self.order_repository.get_order_items(order_id)
            
            for item in order_items:
                product = await self.product_repository.get_by_id(item.product_id)
                if product:
                    new_stock = product.stock_quantity - item.quantity
                    await self.product_repository.update(item.product_id, {"stock_quantity": new_stock})
            
            logger.info(f"Stock reserved for order {order_id}")
            
        except Exception as e:
            logger.error(f"Stock reservation failed for order {order_id}: {e}")
            raise
    
    async def _confirm_stock_reservation(self, order_id: int) -> None:
        """Confirm stock reservation (already deducted)"""
        logger.info(f"Stock reservation confirmed for order {order_id}")
    
    async def _release_stock(self, order_id: int) -> None:
        """Release reserved stock"""
        try:
            order_items = await self.order_repository.get_order_items(order_id)
            
            for item in order_items:
                product = await self.product_repository.get_by_id(item.product_id)
                if product:
                    new_stock = product.stock_quantity + item.quantity
                    await self.product_repository.update(item.product_id, {"stock_quantity": new_stock})
            
            logger.info(f"Stock released for order {order_id}")
            
        except Exception as e:
            logger.error(f"Stock release failed for order {order_id}: {e}")
            raise
    
    async def get_order_statistics(self) -> Dict[str, Any]:
        """Get order statistics"""
        try:
            total_orders = await self.count()
            
            # Get orders by status
            status_counts = await self.order_repository.get_orders_by_status_count()
            
            # Get revenue statistics
            revenue_stats = await self.order_repository.get_revenue_statistics()
            
            # Get recent orders count
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_orders = await self.order_repository.get_orders_since_date(thirty_days_ago)
            
            stats = {
                "total_orders": total_orders,
                "status_counts": status_counts,
                "revenue_statistics": revenue_stats,
                "recent_orders_count": len(recent_orders),
                "average_order_value": revenue_stats.get("average_order_value", 0)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting order statistics: {e}")
            raise
    
    async def get_user_order_history(self, user_id: int) -> List[Order]:
        """Get user's order history"""
        try:
            return await self.order_repository.get_user_orders(user_id)
        except Exception as e:
            logger.error(f"Error getting user order history: {e}")
            raise
    
    async def get_orders_by_status(self, status: str) -> List[Order]:
        """Get orders by status"""
        try:
            return await self.get_all(filters={"status": status})
        except Exception as e:
            logger.error(f"Error getting orders by status: {e}")
            raise
    
    async def get_user_orders_by_status(self, user_id: int, status: str) -> List[Order]:
        """Get user orders by status"""
        try:
            return await self.get_all(filters={"user_id": user_id, "status": status})
        except Exception as e:
            logger.error(f"Error getting user orders by status: {e}")
            raise
    
    async def add_order_item(self, order_id: int, item_data: Dict[str, Any]) -> Order:
        """Add item to existing order"""
        try:
            order = await self.get_by_id_or_raise(order_id)
            
            # Validate that order can be modified
            if order.status not in ['pending', 'confirmed']:
                raise BusinessLogicError("Cannot add items to order in current status")
            
            # Validate product
            product = await self.product_repository.get_by_id(item_data['product_id'])
            if not product:
                raise NotFoundError(f"Product with ID {item_data['product_id']} not found")
            
            if not product.is_available:
                raise BusinessLogicError(f"Product '{product.name}' is not available")
            
            if product.stock_quantity < item_data['quantity']:
                raise BusinessLogicError(f"Insufficient stock for product '{product.name}'")
            
            # Add item
            await self.order_repository.create_order_item(order_id, item_data)
            
            # Recalculate order totals
            await self._recalculate_order_totals(order_id)
            
            return await self.get_by_id(order_id)
            
        except Exception as e:
            logger.error(f"Add order item failed: {e}")
            raise
    
    async def remove_order_item(self, order_id: int, item_id: int) -> Order:
        """Remove item from order"""
        try:
            order = await self.get_by_id_or_raise(order_id)
            
            # Validate that order can be modified
            if order.status not in ['pending', 'confirmed']:
                raise BusinessLogicError("Cannot remove items from order in current status")
            
            # Remove item
            await self.order_repository.delete_order_item(item_id)
            
            # Recalculate order totals
            await self._recalculate_order_totals(order_id)
            
            return await self.get_by_id(order_id)
            
        except Exception as e:
            logger.error(f"Remove order item failed: {e}")
            raise
    
    async def _recalculate_order_totals(self, order_id: int) -> None:
        """Recalculate order totals after item changes"""
        try:
            order_items = await self.order_repository.get_order_items(order_id)
            
            subtotal = Decimal('0.00')
            tax_amount = Decimal('0.00')
            
            for item in order_items:
                product = await self.product_repository.get_by_id(item.product_id)
                if product:
                    item_total = Decimal(str(product.price)) * item.quantity
                    subtotal += item_total
                    
                    if product.tax_rate:
                        tax_amount += item_total * Decimal(str(product.tax_rate))
            
            # Get shipping cost (simplified)
            shipping_cost = Decimal('9.99') if subtotal < Decimal('100.00') else Decimal('0.00')
            total_amount = subtotal + tax_amount + shipping_cost
            
            # Update order totals
            await self.update(order_id, {
                "subtotal": float(subtotal),
                "tax_amount": float(tax_amount),
                "shipping_cost": float(shipping_cost),
                "total_amount": float(total_amount)
            })
            
        except Exception as e:
            logger.error(f"Recalculate order totals failed: {e}")
            raise
    
    async def get_recent_orders(self, days: int = 30) -> List[Order]:
        """Get recent orders"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            return await self.order_repository.get_orders_since_date(since_date)
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            raise
    
    async def get_user_recent_orders(self, user_id: int, days: int = 30) -> List[Order]:
        """Get user's recent orders"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            return await self.order_repository.get_user_orders_since_date(user_id, since_date)
        except Exception as e:
            logger.error(f"Error getting user recent orders: {e}")
            raise
