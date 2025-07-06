"""
Orders repositories.
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime
import logging

from app.models.order import Order, OrderItem
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class OrderRepository:
    """Order repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, order_data: dict, order_items: List[dict]) -> Order:
        """Create a new order with items."""
        try:
            order = Order(**order_data)
            self.db.add(order)
            self.db.flush()  # Get the order ID
            
            # Create order items
            for item_data in order_items:
                item_data["order_id"] = order.id
                order_item = OrderItem(**item_data)
                self.db.add(order_item)
            
            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        try:
            return self.db.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            logger.error(f"Error getting order by ID: {str(e)}")
            raise
    
    def get_by_id_sync(self, order_id: int) -> Optional[Order]:
        """Get order by ID (synchronous version for thread pool)."""
        try:
            return self.db.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            logger.error(f"Error getting order by ID (sync): {str(e)}")
            raise
    
    async def get_multi(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """Get multiple orders with pagination and filtering."""
        try:
            query = self.db.query(Order)
            
            # Apply filters
            if user_id:
                query = query.filter(Order.user_id == user_id)
            
            if status_filter:
                query = query.filter(Order.status == status_filter)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
            
            return orders, total
        
        except Exception as e:
            logger.error(f"Error getting multiple orders: {str(e)}")
            raise
    
    async def update(self, order_id: int, update_data: dict) -> Optional[Order]:
        """Update order."""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(order, field):
                    setattr(order, field, value)
            
            order.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(order)
            
            return order
        
        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            self.db.rollback()
            raise
    
    async def delete(self, order_id: int) -> bool:
        """Delete order."""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return False
            
            # Delete order items first
            self.db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()
            
            # Delete order
            self.db.delete(order)
            self.db.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting order: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_user_orders(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Order], int]:
        """Get orders for a specific user."""
        try:
            query = self.db.query(Order).filter(Order.user_id == user_id)
            
            total = query.count()
            orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
            
            return orders, total
        
        except Exception as e:
            logger.error(f"Error getting user orders: {str(e)}")
            raise
    
    async def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get order items."""
        try:
            return self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        except Exception as e:
            logger.error(f"Error getting order items: {str(e)}")
            raise
    
    async def get_orders_by_status(self, status: str, limit: int = 100) -> List[Order]:
        """Get orders by status."""
        try:
            return (
                self.db.query(Order)
                .filter(Order.status == status)
                .order_by(desc(Order.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting orders by status: {str(e)}")
            raise
    
    async def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Order]:
        """Get orders within date range."""
        try:
            return (
                self.db.query(Order)
                .filter(
                    and_(
                        Order.created_at >= start_date,
                        Order.created_at <= end_date,
                    )
                )
                .order_by(desc(Order.created_at))
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting orders by date range: {str(e)}")
            raise
    
    def calculate_order_stats_sync(self, order_id: int) -> Dict[str, Any]:
        """Calculate order statistics (synchronous for thread pool)."""
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return {}
            
            # Get order items
            items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            
            # Calculate processing time
            processing_time = 0
            if order.updated_at and order.created_at:
                processing_time = (order.updated_at - order.created_at).total_seconds()
            
            return {
                "total_amount": float(order.total_amount),
                "item_count": len(items),
                "processing_time": processing_time,
                "shipping_cost": 0.0,  # Would be calculated based on shipping method
                "tax_amount": float(order.total_amount) * 0.08,  # 8% tax
                "discount_amount": 0.0,  # Would be calculated based on discounts
            }
        
        except Exception as e:
            logger.error(f"Error calculating order stats: {str(e)}")
            raise
    
    async def get_user_order_summary(self, user_id: int) -> Dict[str, Any]:
        """Get order summary for user."""
        try:
            # Get order counts by status
            status_counts = (
                self.db.query(Order.status, func.count(Order.id))
                .filter(Order.user_id == user_id)
                .group_by(Order.status)
                .all()
            )
            
            # Get total spent
            total_spent = (
                self.db.query(func.sum(Order.total_amount))
                .filter(Order.user_id == user_id)
                .scalar() or 0.0
            )
            
            # Get order count
            total_orders = (
                self.db.query(func.count(Order.id))
                .filter(Order.user_id == user_id)
                .scalar() or 0
            )
            
            return {
                "total_orders": total_orders,
                "total_spent": float(total_spent),
                "status_counts": {status: count for status, count in status_counts},
                "average_order_value": float(total_spent) / total_orders if total_orders > 0 else 0.0,
            }
        
        except Exception as e:
            logger.error(f"Error getting user order summary: {str(e)}")
            raise
    
    async def get_recent_orders(self, limit: int = 10) -> List[Order]:
        """Get recent orders."""
        try:
            return (
                self.db.query(Order)
                .order_by(desc(Order.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting recent orders: {str(e)}")
            raise
    
    async def get_pending_orders(self) -> List[Order]:
        """Get pending orders."""
        try:
            return (
                self.db.query(Order)
                .filter(Order.status == "pending")
                .order_by(Order.created_at)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting pending orders: {str(e)}")
            raise
