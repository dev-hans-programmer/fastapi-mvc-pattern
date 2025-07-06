"""
Products repositories.
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime
import logging

from app.models.product import Product
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ProductRepository:
    """Product repository."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, product_data: dict) -> Product:
        """Create a new product."""
        try:
            product = Product(**product_data)
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            self.db.rollback()
            raise
    
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        try:
            return self.db.query(Product).filter(Product.id == product_id).first()
        except Exception as e:
            logger.error(f"Error getting product by ID: {str(e)}")
            raise
    
    def get_by_id_sync(self, product_id: int) -> Optional[Product]:
        """Get product by ID (synchronous version for thread pool)."""
        try:
            return self.db.query(Product).filter(Product.id == product_id).first()
        except Exception as e:
            logger.error(f"Error getting product by ID (sync): {str(e)}")
            raise
    
    async def get_by_name(self, name: str) -> Optional[Product]:
        """Get product by name."""
        try:
            return self.db.query(Product).filter(Product.name == name).first()
        except Exception as e:
            logger.error(f"Error getting product by name: {str(e)}")
            raise
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Product], int]:
        """Get multiple products with pagination and filtering."""
        try:
            query = self.db.query(Product)
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                    )
                )
            
            if category:
                query = query.filter(Product.category == category)
            
            if min_price is not None:
                query = query.filter(Product.price >= min_price)
            
            if max_price is not None:
                query = query.filter(Product.price <= max_price)
            
            if is_active is not None:
                query = query.filter(Product.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            products = query.offset(skip).limit(limit).all()
            
            return products, total
        
        except Exception as e:
            logger.error(f"Error getting multiple products: {str(e)}")
            raise
    
    async def update(self, product_id: int, update_data: dict) -> Optional[Product]:
        """Update product."""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(product)
            
            return product
        
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            self.db.rollback()
            raise
    
    async def delete(self, product_id: int) -> bool:
        """Delete product."""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            self.db.delete(product)
            self.db.commit()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            self.db.rollback()
            raise
    
    async def search_products(self, search_term: str, limit: int = 10) -> List[Product]:
        """Search products by name or description."""
        try:
            search_pattern = f"%{search_term}%"
            return (
                self.db.query(Product)
                .filter(
                    and_(
                        Product.is_active == True,
                        or_(
                            Product.name.ilike(search_pattern),
                            Product.description.ilike(search_pattern),
                        )
                    )
                )
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            raise
    
    async def get_categories(self) -> List[str]:
        """Get all product categories."""
        try:
            result = (
                self.db.query(Product.category)
                .filter(Product.is_active == True)
                .distinct()
                .all()
            )
            return [row[0] for row in result if row[0]]
        except Exception as e:
            logger.error(f"Error getting categories: {str(e)}")
            raise
    
    async def get_by_category(self, category: str, limit: int = 100) -> List[Product]:
        """Get products by category."""
        try:
            return (
                self.db.query(Product)
                .filter(
                    and_(
                        Product.category == category,
                        Product.is_active == True,
                    )
                )
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting products by category: {str(e)}")
            raise
    
    async def update_inventory(self, product_id: int, quantity: int) -> bool:
        """Update product inventory."""
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return False
            
            product.inventory_count = quantity
            product.updated_at = datetime.utcnow()
            self.db.commit()
            
            return True
        
        except Exception as e:
            logger.error(f"Error updating inventory: {str(e)}")
            self.db.rollback()
            raise
    
    def calculate_product_stats_sync(self, product_id: int) -> Dict[str, Any]:
        """Calculate product statistics (synchronous for thread pool)."""
        try:
            # This would typically perform complex calculations
            # For now, return mock data
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {}
            
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "average_rating": 0.0,
                "view_count": 0,
                "inventory_level": product.inventory_count,
                "last_order_date": None,
            }
        
        except Exception as e:
            logger.error(f"Error calculating product stats: {str(e)}")
            raise
    
    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products."""
        try:
            return (
                self.db.query(Product)
                .filter(
                    and_(
                        Product.is_active == True,
                        Product.is_featured == True,
                    )
                )
                .order_by(desc(Product.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting featured products: {str(e)}")
            raise
    
    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock."""
        try:
            return (
                self.db.query(Product)
                .filter(
                    and_(
                        Product.is_active == True,
                        Product.inventory_count <= threshold,
                    )
                )
                .order_by(Product.inventory_count)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting low stock products: {str(e)}")
            raise
    
    async def get_popular_products(self, limit: int = 10) -> List[Product]:
        """Get popular products based on orders."""
        try:
            # This would typically join with orders table
            # For now, return products ordered by created_at
            return (
                self.db.query(Product)
                .filter(Product.is_active == True)
                .order_by(desc(Product.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting popular products: {str(e)}")
            raise
