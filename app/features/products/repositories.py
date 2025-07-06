"""
Product repositories
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_repository import BaseRepository
from app.features.products.types import Product

logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository[Product]):
    """Product repository"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Product)
    
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        try:
            return await self.get_by_field("sku", sku)
        except Exception as e:
            logger.error(f"Error getting product by SKU: {e}")
            raise
    
    async def get_products_by_category(self, category: str) -> List[Product]:
        """Get products by category"""
        try:
            return await self.get_all(filters={"category": category})
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            raise
    
    async def get_available_products(self, limit: int = None) -> List[Product]:
        """Get available products"""
        try:
            return await self.get_all(
                filters={"is_available": True},
                limit=limit or 1000
            )
        except Exception as e:
            logger.error(f"Error getting available products: {e}")
            raise
    
    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products"""
        try:
            return await self.get_all(
                filters={"is_featured": True, "is_available": True},
                limit=limit,
                order_by="created_at",
                order_desc=True
            )
        except Exception as e:
            logger.error(f"Error getting featured products: {e}")
            raise
    
    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock"""
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.stock_quantity <= threshold,
                    self.model.stock_quantity > 0,
                    self.model.is_available == True
                )
            )
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            raise
    
    async def get_out_of_stock_products(self) -> List[Product]:
        """Get out of stock products"""
        try:
            return await self.get_all(filters={"stock_quantity": 0})
        except Exception as e:
            logger.error(f"Error getting out of stock products: {e}")
            raise
    
    async def search_products(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Search products by name, description, or SKU"""
        try:
            stmt = select(self.model).where(
                or_(
                    self.model.name.ilike(f"%{search_term}%"),
                    self.model.description.ilike(f"%{search_term}%"),
                    self.model.sku.ilike(f"%{search_term}%")
                )
            ).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise
    
    async def search_products_advanced(
        self,
        search_term: str = None,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        in_stock: bool = None,
        is_featured: bool = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Advanced product search with filters"""
        try:
            stmt = select(self.model)
            conditions = []
            
            # Text search
            if search_term:
                conditions.append(
                    or_(
                        self.model.name.ilike(f"%{search_term}%"),
                        self.model.description.ilike(f"%{search_term}%"),
                        self.model.sku.ilike(f"%{search_term}%")
                    )
                )
            
            # Category filter
            if category:
                conditions.append(self.model.category == category)
            
            # Price range filter
            if min_price is not None:
                conditions.append(self.model.price >= min_price)
            
            if max_price is not None:
                conditions.append(self.model.price <= max_price)
            
            # Stock filter
            if in_stock is not None:
                if in_stock:
                    conditions.append(self.model.stock_quantity > 0)
                else:
                    conditions.append(self.model.stock_quantity == 0)
            
            # Featured filter
            if is_featured is not None:
                conditions.append(self.model.is_featured == is_featured)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error in advanced product search: {e}")
            raise
    
    async def get_products_by_price_range(
        self,
        min_price: float,
        max_price: float,
        limit: int = 100
    ) -> List[Product]:
        """Get products within a price range"""
        try:
            stmt = select(self.model).where(
                and_(
                    self.model.price >= min_price,
                    self.model.price <= max_price,
                    self.model.is_available == True
                )
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting products by price range: {e}")
            raise
    
    async def get_product_categories(self) -> List[str]:
        """Get distinct product categories"""
        try:
            stmt = select(self.model.category).distinct()
            result = await self.session.execute(stmt)
            return [row[0] for row in result.fetchall() if row[0]]
            
        except Exception as e:
            logger.error(f"Error getting product categories: {e}")
            raise
    
    async def get_product_stats(self) -> Dict[str, Any]:
        """Get product statistics"""
        try:
            total_products = await self.count()
            available_products = await self.count({"is_available": True})
            featured_products = await self.count({"is_featured": True})
            
            # Get stock statistics
            stock_stats = await self.session.execute(
                select(
                    func.sum(self.model.stock_quantity).label('total_stock'),
                    func.avg(self.model.stock_quantity).label('avg_stock'),
                    func.min(self.model.stock_quantity).label('min_stock'),
                    func.max(self.model.stock_quantity).label('max_stock')
                )
            )
            stock_result = stock_stats.first()
            
            # Get price statistics
            price_stats = await self.session.execute(
                select(
                    func.avg(self.model.price).label('avg_price'),
                    func.min(self.model.price).label('min_price'),
                    func.max(self.model.price).label('max_price')
                ).where(self.model.is_available == True)
            )
            price_result = price_stats.first()
            
            return {
                "total_products": total_products,
                "available_products": available_products,
                "unavailable_products": total_products - available_products,
                "featured_products": featured_products,
                "stock_statistics": {
                    "total_stock": int(stock_result.total_stock or 0),
                    "average_stock": float(stock_result.avg_stock or 0),
                    "minimum_stock": int(stock_result.min_stock or 0),
                    "maximum_stock": int(stock_result.max_stock or 0)
                },
                "price_statistics": {
                    "average_price": float(price_result.avg_price or 0),
                    "minimum_price": float(price_result.min_price or 0),
                    "maximum_price": float(price_result.max_price or 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting product stats: {e}")
            raise
    
    async def get_stock_statistics(self) -> Dict[str, Any]:
        """Get detailed stock statistics"""
        try:
            # Get products with different stock levels
            zero_stock = await self.count({"stock_quantity": 0})
            low_stock = len(await self.get_low_stock_products(10))
            
            # Get total stock value
            stock_value_result = await self.session.execute(
                select(
                    func.sum(self.model.stock_quantity * self.model.price).label('total_value')
                ).where(self.model.is_available == True)
            )
            total_stock_value = stock_value_result.scalar() or 0
            
            return {
                "zero_stock_products": zero_stock,
                "low_stock_products": low_stock,
                "total_stock_value": float(total_stock_value)
            }
            
        except Exception as e:
            logger.error(f"Error getting stock statistics: {e}")
            raise
    
    async def check_sku_exists(self, sku: str, exclude_product_id: int = None) -> bool:
        """Check if SKU exists"""
        try:
            stmt = select(func.count(self.model.id)).where(
                self.model.sku == sku
            )
            
            if exclude_product_id:
                stmt = stmt.where(self.model.id != exclude_product_id)
            
            result = await self.session.execute(stmt)
            return result.scalar() > 0
            
        except Exception as e:
            logger.error(f"Error checking SKU existence: {e}")
            raise
    
    async def update_stock_quantity(self, product_id: int, quantity: int) -> bool:
        """Update product stock quantity"""
        try:
            stmt = update(self.model).where(
                self.model.id == product_id
            ).values(stock_quantity=quantity)
            
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating stock quantity: {e}")
            raise
    
    async def bulk_update_prices(self, price_updates: List[Dict[str, Any]]) -> int:
        """Bulk update product prices"""
        try:
            updated_count = 0
            
            for update in price_updates:
                if 'id' not in update or 'price' not in update:
                    continue
                
                stmt = update(self.model).where(
                    self.model.id == update['id']
                ).values(price=update['price'])
                
                result = await self.session.execute(stmt)
                updated_count += result.rowcount
            
            await self.session.commit()
            return updated_count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error bulk updating prices: {e}")
            raise
    
    async def get_products_for_export(self, filters: Dict[str, Any] = None) -> List[Product]:
        """Get products for export with optional filters"""
        try:
            return await self.get_all(filters=filters, limit=10000)
        except Exception as e:
            logger.error(f"Error getting products for export: {e}")
            raise
    
    async def get_recently_added_products(self, days: int = 7, limit: int = 20) -> List[Product]:
        """Get recently added products"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = select(self.model).where(
                self.model.created_at >= cutoff_date
            ).order_by(self.model.created_at.desc()).limit(limit)
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting recently added products: {e}")
            raise
    
    async def get_products_updated_since(self, since_date: datetime) -> List[Product]:
        """Get products updated since a specific date"""
        try:
            stmt = select(self.model).where(
                self.model.updated_at >= since_date
            ).order_by(self.model.updated_at.desc())
            
            result = await self.session.execute(stmt)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting products updated since date: {e}")
            raise
