"""
Order repositories
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.base_repository import BaseRepository
from app.features.orders.types import Order, OrderItem

logger = logging.getLogger(__name__)


class OrderRepository(BaseRepository[Order]):
    """Order repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)
    
    async def get_order_with_items(self, order_id: int) -> Optional[Order]:
        """Get order with its items"""
        try:
            stmt = select(self.model).options(
                selectinload(self.model.items)
            ).where(self.model.id == order_id)
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting order with items: {e}")
            raise
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        try:
            return await self.get_all(
                filters={"user_id": user_id},
                order_by="created_at",
                order_desc=True
            )
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            raise
    
    async def get_orders_by_status(self, status: str) -> List[Order]:
        """Get orders by status"""
        try:
            return await self.get_all(filters={"status": status})
        except Exception as e:
            logger.error(f"Error getting orders by status: {e}")
            raise
    
    async def get_orders_by_status_count(self) -> Dict[str, int]:
        """Get count of orders by status"""
        try:
            stmt = select(
                self.model.status,
                func.count(self.model.id).label('count')
            ).group_by(self.model.status)
            
            result = await self.session.execute(stmt)
            return {row.status: row.count for row in result.fetchall()}
            
        except Exception as e:
            logger.error(f"Error getting orders by status count: {e}")
            raise
    
    async def get_orders_since_date(self, since_date: datetime) -> List[Order]:
        """Get orders since a specific date"""
        try:
            stmt = select(self.model).where(
                self.model.created_at >= since_date
            ).order_by(self.model.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting orders since date: {e}")
            raise
    
    async def get_user_orders_since_date(self, user_id: int, since_date: datetime) -> List[Order]:
        """Get user orders since a specific date"""
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.created_at >= since_date
                )
            ).order_by(self.model.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user orders since date: {e}")
            raise
    
    async def get_revenue_statistics(self) -> Dict[str, Any]:
        """Get revenue statistics"""
        try:
            # Total revenue
            total_revenue_result = await self.session.execute(
                select(func.sum(self.model.total_amount)).where(
                    self.model.status.in_(['delivered', 'shipped'])
                )
            )
            total_revenue = total_revenue_result.scalar() or 0
            
            # Average order value
            avg_order_result = await self.session.execute(
                select(func.avg(self.model.total_amount)).where(
                    self.model.status.in_(['delivered', 'shipped'])
                )
            )
            avg_order_value = avg_order_result.scalar() or 0
            
            # Monthly revenue (last 12 months)
            twelve_months_ago = datetime.utcnow() - timedelta(days=365)
            monthly_revenue_result = await self.session.execute(
                select(
                    func.date_trunc('month', self.model.created_at).label('month'),
                    func.sum(self.model.total_amount).label('revenue')
                ).where(
                    and_(
                        self.model.created_at >= twelve_months_ago,
                        self.model.status.in_(['delivered', 'shipped'])
                    )
                ).group_by(func.date_trunc('month', self.model.created_at))
                .order_by(func.date_trunc('month', self.model.created_at))
            )
            
            monthly_revenue = {
                row.month.strftime('%Y-%m'): float(row.revenue)
                for row in monthly_revenue_result.fetchall()
            }
            
            return {
                "total_revenue": float(total_revenue),
                "average_order_value": float(avg_order_value),
                "monthly_revenue": monthly_revenue
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue statistics: {e}")
            raise
    
    async def search_orders(
        self,
        search_term: str,
        user_id: int = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Search orders by order number or customer info"""
        try:
            stmt = select(self.model).where(
                or_(
                    self.model.order_number.ilike(f"%{search_term}%"),
                    self.model.shipping_address['name'].astext.ilike(f"%{search_term}%"),
                    self.model.billing_address['name'].astext.ilike(f"%{search_term}%")
                )
            )
            
            if user_id:
                stmt = stmt.where(self.model.user_id == user_id)
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching orders: {e}")
            raise
    
    async def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get items for an order"""
        try:
            stmt = select(OrderItem).where(OrderItem.order_id == order_id)
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting order items: {e}")
            raise
    
    async def create_order_item(self, order_id: int, item_data: Dict[str, Any]) -> OrderItem:
        """Create an order item"""
        try:
            item_data["order_id"] = order_id
            
            # Get product to set price at time of order
            from app.features.products.types import Product
            product_result = await self.session.execute(
                select(Product).where(Product.id == item_data["product_id"])
            )
            product = product_result.scalar_one_or_none()
            
            if product:
                item_data["unit_price"] = float(product.price)
                item_data["total_price"] = float(product.price) * item_data["quantity"]
            
            order_item = OrderItem(**item_data)
            self.session.add(order_item)
            await self.session.commit()
            await self.session.refresh(order_item)
            
            return order_item
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating order item: {e}")
            raise
    
    async def update_order_item(self, item_id: int, update_data: Dict[str, Any]) -> OrderItem:
        """Update an order item"""
        try:
            stmt = select(OrderItem).where(OrderItem.id == item_id)
            result = await self.session.execute(stmt)
            order_item = result.scalar_one_or_none()
            
            if not order_item:
                raise ValueError(f"Order item with id {item_id} not found")
            
            for key, value in update_data.items():
                if hasattr(order_item, key):
                    setattr(order_item, key, value)
            
            # Recalculate total price if quantity or unit price changed
            if 'quantity' in update_data or 'unit_price' in update_data:
                order_item.total_price = order_item.unit_price * order_item.quantity
            
            await self.session.commit()
            await self.session.refresh(order_item)
            
            return order_item
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating order item: {e}")
            raise
    
    async def delete_order_item(self, item_id: int) -> bool:
        """Delete an order item"""
        try:
            stmt = select(OrderItem).where(OrderItem.id == item_id)
            result = await self.session.execute(stmt)
            order_item = result.scalar_one_or_none()
            
            if not order_item:
                return False
            
            await self.session.delete(order_item)
            await self.session.commit()
            
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting order item: {e}")
            raise
    
    async def get_orders_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: int = None
    ) -> List[Order]:
        """Get orders within a date range"""
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.created_at >= start_date,
                    self.model.created_at <= end_date
                )
            )
            
            if user_id:
                stmt = stmt.where(self.model.user_id == user_id)
            
            stmt = stmt.order_by(self.model.created_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting orders by date range: {e}")
            raise
    
    async def get_top_customers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top customers by order value"""
        try:
            stmt = select(
                self.model.user_id,
                func.count(self.model.id).label('order_count'),
                func.sum(self.model.total_amount).label('total_spent')
            ).where(
                self.model.status.in_(['delivered', 'shipped'])
            ).group_by(self.model.user_id).order_by(
                func.sum(self.model.total_amount).desc()
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            return [
                {
                    "user_id": row.user_id,
                    "order_count": row.order_count,
                    "total_spent": float(row.total_spent)
                }
                for row in result.fetchall()
            ]
            
        except Exception as e:
            logger.error(f"Error getting top customers: {e}")
            raise
    
    async def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        try:
            return await self.get_orders_by_status("pending")
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            raise
    
    async def get_orders_needing_shipment(self) -> List[Order]:
        """Get orders that need to be shipped"""
        try:
            return await self.get_orders_by_status("processing")
        except Exception as e:
            logger.error(f"Error getting orders needing shipment: {e}")
            raise
