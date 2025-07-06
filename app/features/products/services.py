"""
Product services
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.exceptions import NotFoundError, ValidationError, BusinessLogicError
from app.features.products.repositories import ProductRepository
from app.features.products.types import Product, ProductCreate, ProductUpdate
from app.common.base_service import BaseService
from app.common.validators import BaseValidator

logger = logging.getLogger(__name__)


class ProductService(BaseService[Product, ProductCreate, ProductUpdate]):
    """Product service"""
    
    def __init__(self, product_repository: ProductRepository):
        super().__init__(product_repository)
        self.product_repository = product_repository
    
    async def _validate_create(self, obj_in: ProductCreate) -> None:
        """Validate product creation"""
        # Check if SKU already exists
        if obj_in.sku:
            existing_product = await self.product_repository.get_by_field("sku", obj_in.sku)
            if existing_product:
                raise ValidationError("SKU already exists")
        
        # Validate price
        if obj_in.price <= 0:
            raise ValidationError("Price must be greater than 0")
        
        # Validate stock quantity
        if obj_in.stock_quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")
    
    async def _validate_update(self, db_obj: Product, obj_in: ProductUpdate) -> None:
        """Validate product update"""
        # Check if SKU is being changed and if it already exists
        if obj_in.sku and obj_in.sku != db_obj.sku:
            existing_product = await self.product_repository.get_by_field("sku", obj_in.sku)
            if existing_product:
                raise ValidationError("SKU already exists")
        
        # Validate price
        if obj_in.price is not None and obj_in.price <= 0:
            raise ValidationError("Price must be greater than 0")
        
        # Validate stock quantity
        if obj_in.stock_quantity is not None and obj_in.stock_quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")
    
    async def _pre_create(self, obj_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-create processing"""
        # Set default values
        obj_data.setdefault("is_available", True)
        obj_data.setdefault("is_featured", False)
        
        # Generate SKU if not provided
        if not obj_data.get("sku"):
            obj_data["sku"] = await self._generate_sku(obj_data.get("name", ""))
        
        return obj_data
    
    async def _generate_sku(self, product_name: str) -> str:
        """Generate SKU for product"""
        import re
        import secrets
        
        # Clean product name and take first 3 words
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', product_name).upper()
        words = clean_name.split()[:3]
        name_part = ''.join(word[:3] for word in words)
        
        # Add random suffix
        random_part = secrets.token_hex(3).upper()
        
        return f"{name_part}-{random_part}"
    
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        try:
            return await self.product_repository.get_by_field("sku", sku)
        except Exception as e:
            logger.error(f"Error getting product by SKU: {e}")
            raise
    
    async def get_products_by_category(self, category: str) -> List[Product]:
        """Get products by category"""
        try:
            return await self.product_repository.get_all(
                filters={"category": category, "is_available": True}
            )
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            raise
    
    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products"""
        try:
            return await self.product_repository.get_all(
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
            return await self.product_repository.get_low_stock_products(threshold)
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            raise
    
    async def update_stock(self, product_id: int, quantity: int) -> Product:
        """Update product stock"""
        try:
            product = await self.get_by_id_or_raise(product_id)
            
            if quantity < 0:
                raise ValidationError("Stock quantity cannot be negative")
            
            updated_product = await self.update(product_id, {"stock_quantity": quantity})
            
            logger.info(f"Stock updated for product {product_id}: {quantity}")
            return updated_product
            
        except Exception as e:
            logger.error(f"Error updating product stock: {e}")
            raise
    
    async def adjust_stock(self, product_id: int, adjustment: int) -> Product:
        """Adjust product stock by a delta amount"""
        try:
            product = await self.get_by_id_or_raise(product_id)
            
            new_quantity = product.stock_quantity + adjustment
            
            if new_quantity < 0:
                raise BusinessLogicError("Insufficient stock")
            
            updated_product = await self.update(product_id, {"stock_quantity": new_quantity})
            
            logger.info(f"Stock adjusted for product {product_id}: {adjustment} (new total: {new_quantity})")
            return updated_product
            
        except Exception as e:
            logger.error(f"Error adjusting product stock: {e}")
            raise
    
    async def toggle_availability(self, product_id: int) -> Product:
        """Toggle product availability"""
        try:
            product = await self.get_by_id_or_raise(product_id)
            
            new_availability = not product.is_available
            updated_product = await self.update(product_id, {"is_available": new_availability})
            
            logger.info(f"Product {product_id} availability toggled to {new_availability}")
            return updated_product
            
        except Exception as e:
            logger.error(f"Error toggling product availability: {e}")
            raise
    
    async def set_featured(self, product_id: int, is_featured: bool) -> Product:
        """Set product featured status"""
        try:
            product = await self.get_by_id_or_raise(product_id)
            
            if product.is_featured == is_featured:
                raise BusinessLogicError(f"Product is already {'featured' if is_featured else 'not featured'}")
            
            updated_product = await self.update(product_id, {"is_featured": is_featured})
            
            logger.info(f"Product {product_id} featured status set to {is_featured}")
            return updated_product
            
        except Exception as e:
            logger.error(f"Error setting product featured status: {e}")
            raise
    
    async def update_price(self, product_id: int, new_price: float) -> Product:
        """Update product price"""
        try:
            product = await self.get_by_id_or_raise(product_id)
            
            if new_price <= 0:
                raise ValidationError("Price must be greater than 0")
            
            # Store old price for price history (in a real app)
            old_price = product.price
            
            updated_product = await self.update(product_id, {"price": new_price})
            
            logger.info(f"Price updated for product {product_id}: {old_price} -> {new_price}")
            return updated_product
            
        except Exception as e:
            logger.error(f"Error updating product price: {e}")
            raise
    
    async def get_product_statistics(self) -> Dict[str, Any]:
        """Get product statistics"""
        try:
            total_products = await self.count()
            available_products = await self.count({"is_available": True})
            featured_products = await self.count({"is_featured": True})
            
            # Get products by category
            categories = await self.product_repository.get_product_categories()
            category_counts = {}
            for category in categories:
                category_counts[category] = await self.count({"category": category})
            
            # Get stock statistics
            stock_stats = await self.product_repository.get_stock_statistics()
            
            stats = {
                "total_products": total_products,
                "available_products": available_products,
                "unavailable_products": total_products - available_products,
                "featured_products": featured_products,
                "categories": category_counts,
                "stock_statistics": stock_stats,
                "low_stock_count": len(await self.get_low_stock_products()),
                "out_of_stock_count": await self.count({"stock_quantity": 0})
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting product statistics: {e}")
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
        """Advanced product search"""
        try:
            return await self.product_repository.search_products_advanced(
                search_term=search_term,
                category=category,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock,
                is_featured=is_featured,
                skip=skip,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error in advanced product search: {e}")
            raise
    
    async def get_related_products(self, product_id: int, limit: int = 5) -> List[Product]:
        """Get related products"""
        try:
            product = await self.get_by_id_or_raise(product_id)
            
            # Get products in the same category
            related_products = await self.product_repository.get_all(
                filters={
                    "category": product.category,
                    "is_available": True
                },
                limit=limit + 1,  # +1 to exclude the current product
                order_by="created_at",
                order_desc=True
            )
            
            # Remove the current product from the list
            related_products = [p for p in related_products if p.id != product_id][:limit]
            
            return related_products
            
        except Exception as e:
            logger.error(f"Error getting related products: {e}")
            raise
    
    async def bulk_update_prices(self, price_updates: List[Dict[str, Any]]) -> int:
        """Bulk update product prices"""
        try:
            valid_updates = []
            
            for update in price_updates:
                if "id" not in update or "price" not in update:
                    continue
                
                if update["price"] <= 0:
                    continue
                
                valid_updates.append(update)
            
            updated_count = await self.product_repository.bulk_update(valid_updates)
            
            logger.info(f"Bulk price update completed: {updated_count} products updated")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error in bulk price update: {e}")
            raise
    
    async def get_products_by_price_range(
        self,
        min_price: float,
        max_price: float,
        limit: int = 100
    ) -> List[Product]:
        """Get products within a price range"""
        try:
            return await self.product_repository.get_products_by_price_range(
                min_price, max_price, limit
            )
        except Exception as e:
            logger.error(f"Error getting products by price range: {e}")
            raise
    
    async def export_products(self, format: str = "csv") -> Dict[str, Any]:
        """Export products"""
        try:
            products = await self.get_all()
            
            if format.lower() == "csv":
                export_data = {
                    "format": "csv",
                    "filename": f"products_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                    "record_count": len(products),
                    "download_url": "/api/v1/products/export/download/csv"
                }
            elif format.lower() == "json":
                export_data = {
                    "format": "json",
                    "filename": f"products_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
                    "record_count": len(products),
                    "download_url": "/api/v1/products/export/download/json"
                }
            else:
                raise ValidationError("Invalid export format. Supported formats: csv, json")
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting products: {e}")
            raise
