"""
Products services.
"""
from typing import List, Optional, Tuple, Dict, Any
import logging
from datetime import datetime

from app.features.products.repositories import ProductRepository
from app.features.products.types import ProductCreate, ProductUpdate, ProductStatsResponse
from app.models.product import Product
from app.core.exceptions import NotFoundException, ConflictException
from app.core.thread_pool import AsyncBatchProcessor
from app.tasks.product_tasks import update_product_search_index, notify_product_update

logger = logging.getLogger(__name__)


class ProductService:
    """Product service."""
    
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create a new product."""
        try:
            # Check if product with same name already exists
            existing_product = await self.product_repository.get_by_name(product_data.name)
            if existing_product:
                raise ConflictException("Product with this name already exists")
            
            # Create product
            product_dict = product_data.dict()
            product = await self.product_repository.create(product_dict)
            
            # Update search index (background task)
            update_product_search_index.delay(product.id)
            
            logger.info(f"Product created: {product.name}")
            return product
        
        except Exception as e:
            logger.error(f"Error in create_product: {str(e)}")
            raise
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        try:
            return await self.product_repository.get_by_id(product_id)
        except Exception as e:
            logger.error(f"Error in get_product_by_id: {str(e)}")
            raise
    
    async def get_product_by_name(self, name: str) -> Optional[Product]:
        """Get product by name."""
        try:
            return await self.product_repository.get_by_name(name)
        except Exception as e:
            logger.error(f"Error in get_product_by_name: {str(e)}")
            raise
    
    async def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Product], int]:
        """Get list of products with pagination and filtering."""
        try:
            return await self.product_repository.get_multi(
                skip=skip,
                limit=limit,
                search=search,
                category=category,
                min_price=min_price,
                max_price=max_price,
                is_active=is_active,
            )
        except Exception as e:
            logger.error(f"Error in get_products: {str(e)}")
            raise
    
    async def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """Update product."""
        try:
            # Get existing product
            existing_product = await self.product_repository.get_by_id(product_id)
            if not existing_product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            # Check name uniqueness if name is being updated
            if product_data.name and product_data.name != existing_product.name:
                name_product = await self.product_repository.get_by_name(product_data.name)
                if name_product:
                    raise ConflictException("Product with this name already exists")
            
            # Update product
            update_data = product_data.dict(exclude_unset=True)
            product = await self.product_repository.update(product_id, update_data)
            
            # Notify about update (background task)
            if product:
                notify_product_update.delay(product.id, product.name)
            
            logger.info(f"Product updated: {product.name if product else product_id}")
            return product
        
        except Exception as e:
            logger.error(f"Error in update_product: {str(e)}")
            raise
    
    async def delete_product(self, product_id: int) -> bool:
        """Delete product."""
        try:
            # Check if product exists
            existing_product = await self.product_repository.get_by_id(product_id)
            if not existing_product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            # Soft delete (deactivate) instead of hard delete
            result = await self.product_repository.update(product_id, {"is_active": False})
            
            logger.info(f"Product deactivated: {product_id}")
            return result is not None
        
        except Exception as e:
            logger.error(f"Error in delete_product: {str(e)}")
            raise
    
    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Search products."""
        try:
            return await self.product_repository.search_products(query, limit)
        except Exception as e:
            logger.error(f"Error in search_products: {str(e)}")
            raise
    
    async def get_product_categories(self) -> List[str]:
        """Get all product categories."""
        try:
            return await self.product_repository.get_categories()
        except Exception as e:
            logger.error(f"Error in get_product_categories: {str(e)}")
            raise
    
    def calculate_product_stats(self, product_id: int) -> Optional[ProductStatsResponse]:
        """Calculate product statistics (CPU-intensive operation)."""
        try:
            # This is a CPU-intensive operation that should run in thread pool
            product = self.product_repository.get_by_id_sync(product_id)
            if not product:
                return None
            
            # Simulate heavy computation
            import time
            time.sleep(0.1)  # Simulate processing time
            
            stats_data = self.product_repository.calculate_product_stats_sync(product_id)
            
            return ProductStatsResponse(
                product_id=product_id,
                total_orders=stats_data.get("total_orders", 0),
                total_revenue=stats_data.get("total_revenue", 0.0),
                average_rating=stats_data.get("average_rating", 0.0),
                view_count=stats_data.get("view_count", 0),
                inventory_level=stats_data.get("inventory_level", 0),
                last_order_date=stats_data.get("last_order_date"),
            )
        
        except Exception as e:
            logger.error(f"Error in calculate_product_stats: {str(e)}")
            raise
    
    async def update_product_inventory(self, product_id: int, quantity: int) -> bool:
        """Update product inventory."""
        try:
            # Check if product exists
            existing_product = await self.product_repository.get_by_id(product_id)
            if not existing_product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            # Update inventory
            result = await self.product_repository.update_inventory(product_id, quantity)
            
            logger.info(f"Product inventory updated: {product_id}, quantity: {quantity}")
            return result
        
        except Exception as e:
            logger.error(f"Error in update_product_inventory: {str(e)}")
            raise
    
    async def bulk_update_products(self, product_updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk update products."""
        try:
            results = []
            
            # Use batch processor for concurrent updates
            async with AsyncBatchProcessor(batch_size=10) as processor:
                
                async def process_product_update(update_data: Dict[str, Any]) -> Dict[str, Any]:
                    try:
                        product_id = update_data.get("id")
                        if not product_id:
                            return {"id": None, "status": "error", "message": "Missing product ID"}
                        
                        # Remove id from update data
                        update_fields = {k: v for k, v in update_data.items() if k != "id"}
                        
                        # Update product
                        product = await self.product_repository.update(product_id, update_fields)
                        
                        if product:
                            return {"id": product_id, "status": "success", "message": "Product updated"}
                        else:
                            return {"id": product_id, "status": "error", "message": "Product not found"}
                    
                    except Exception as e:
                        return {"id": product_id, "status": "error", "message": str(e)}
                
                # Process all updates
                results = await processor.process_batch(
                    product_updates,
                    process_product_update
                )
            
            logger.info(f"Bulk update completed: {len(results)} products processed")
            return results
        
        except Exception as e:
            logger.error(f"Error in bulk_update_products: {str(e)}")
            raise
    
    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Get featured products."""
        try:
            return await self.product_repository.get_featured_products(limit)
        except Exception as e:
            logger.error(f"Error in get_featured_products: {str(e)}")
            raise
    
    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock."""
        try:
            return await self.product_repository.get_low_stock_products(threshold)
        except Exception as e:
            logger.error(f"Error in get_low_stock_products: {str(e)}")
            raise
