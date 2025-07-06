"""
Product controllers
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.exceptions import NotFoundError, ValidationError
from app.features.products.services import ProductService
from app.features.products.repositories import ProductRepository
from app.features.products.types import ProductCreate, ProductUpdate, ProductResponse
from app.common.responses import success_response, paginated_response, list_response
from app.common.decorators import timer, log_execution
from app.core.dependencies import CommonQueryParams

logger = logging.getLogger(__name__)


class ProductController:
    """Product controller"""
    
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session
        self.product_repository = ProductRepository(session)
        self.product_service = ProductService(self.product_repository)
    
    @timer
    @log_execution()
    async def create_product(self, product_data: ProductCreate) -> Dict[str, Any]:
        """Create a new product"""
        try:
            product = await self.product_service.create(product_data)
            
            return success_response(
                data=ProductResponse.from_orm(product).dict(),
                message="Product created successfully"
            )
            
        except Exception as e:
            logger.error(f"Product creation failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get product by ID"""
        try:
            product = await self.product_service.get_by_id(product_id)
            
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")
            
            return success_response(
                data=ProductResponse.from_orm(product).dict(),
                message="Product retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get product failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_products(self, params: CommonQueryParams = Depends()) -> Dict[str, Any]:
        """Get all products with pagination"""
        try:
            filters = {}
            if params.search:
                # For search, we'll use the search method instead
                products = await self.product_service.search(
                    search_term=params.search,
                    search_fields=["name", "description", "sku"],
                    skip=params.skip,
                    limit=params.limit
                )
            else:
                products = await self.product_service.get_all(
                    skip=params.skip,
                    limit=params.limit,
                    order_by=params.sort_by,
                    order_desc=params.sort_order == "desc"
                )
            
            # Convert to response models
            product_responses = [ProductResponse.from_orm(product).dict() for product in products]
            
            return list_response(
                data=product_responses,
                message="Products retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get products failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_products_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get products with pagination and filters"""
        try:
            filters = {}
            if category:
                filters["category"] = category
            if in_stock is not None:
                filters["in_stock"] = in_stock
            
            # For price range filtering, we'd need a more sophisticated approach
            # This is simplified for the example
            
            result = await self.product_service.get_paginated(
                page=page,
                page_size=page_size,
                filters=filters,
                order_by="created_at",
                order_desc=True
            )
            
            product_responses = [ProductResponse.from_orm(product).dict() for product in result['records']]
            
            return {
                "success": True,
                "message": "Products retrieved successfully",
                "data": product_responses,
                "pagination": result['pagination']
            }
            
        except Exception as e:
            logger.error(f"Get paginated products failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def update_product(self, product_id: int, product_data: ProductUpdate) -> Dict[str, Any]:
        """Update product"""
        try:
            product = await self.product_service.update(product_id, product_data)
            
            return success_response(
                data=ProductResponse.from_orm(product).dict(),
                message="Product updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Product update failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def delete_product(self, product_id: int) -> Dict[str, Any]:
        """Delete product"""
        try:
            success = await self.product_service.delete(product_id)
            
            if not success:
                raise NotFoundError(f"Product with ID {product_id} not found")
            
            return success_response(
                message="Product deleted successfully"
            )
            
        except Exception as e:
            logger.error(f"Product deletion failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_product_by_sku(self, sku: str) -> Dict[str, Any]:
        """Get product by SKU"""
        try:
            product = await self.product_service.get_by_sku(sku)
            
            if not product:
                raise NotFoundError(f"Product with SKU {sku} not found")
            
            return success_response(
                data=ProductResponse.from_orm(product).dict(),
                message="Product retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get product by SKU failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_products_by_category(self, category: str) -> Dict[str, Any]:
        """Get products by category"""
        try:
            products = await self.product_service.get_products_by_category(category)
            
            product_responses = [ProductResponse.from_orm(product).dict() for product in products]
            
            return list_response(
                data=product_responses,
                message=f"Products in category '{category}' retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get products by category failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def search_products(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search products"""
        try:
            products = await self.product_service.search(
                search_term=search_term,
                search_fields=["name", "description", "sku"],
                skip=skip,
                limit=limit
            )
            
            product_responses = [ProductResponse.from_orm(product).dict() for product in products]
            
            return list_response(
                data=product_responses,
                message="Product search completed"
            )
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def update_product_stock(self, product_id: int, quantity: int) -> Dict[str, Any]:
        """Update product stock"""
        try:
            product = await self.product_service.update_stock(product_id, quantity)
            
            return success_response(
                data=ProductResponse.from_orm(product).dict(),
                message="Product stock updated successfully"
            )
            
        except Exception as e:
            logger.error(f"Product stock update failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_low_stock_products(self, threshold: int = 10) -> Dict[str, Any]:
        """Get products with low stock"""
        try:
            products = await self.product_service.get_low_stock_products(threshold)
            
            product_responses = [ProductResponse.from_orm(product).dict() for product in products]
            
            return list_response(
                data=product_responses,
                message=f"Products with stock below {threshold} retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get low stock products failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_product_statistics(self) -> Dict[str, Any]:
        """Get product statistics"""
        try:
            stats = await self.product_service.get_product_statistics()
            
            return success_response(
                data=stats,
                message="Product statistics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get product statistics failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def bulk_create_products(self, products_data: List[ProductCreate]) -> Dict[str, Any]:
        """Bulk create products"""
        try:
            products = await self.product_service.bulk_create(products_data)
            
            product_responses = [ProductResponse.from_orm(product).dict() for product in products]
            
            return success_response(
                data=product_responses,
                message=f"Successfully created {len(products)} products"
            )
            
        except Exception as e:
            logger.error(f"Bulk product creation failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def bulk_update_products(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update products"""
        try:
            updated_count = await self.product_service.bulk_update(updates)
            
            return success_response(
                data={"updated_count": updated_count},
                message=f"Successfully updated {updated_count} products"
            )
            
        except Exception as e:
            logger.error(f"Bulk product update failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def get_featured_products(self, limit: int = 10) -> Dict[str, Any]:
        """Get featured products"""
        try:
            products = await self.product_service.get_featured_products(limit)
            
            product_responses = [ProductResponse.from_orm(product).dict() for product in products]
            
            return list_response(
                data=product_responses,
                message="Featured products retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Get featured products failed: {e}")
            raise
    
    @timer
    @log_execution()
    async def toggle_product_availability(self, product_id: int) -> Dict[str, Any]:
        """Toggle product availability"""
        try:
            product = await self.product_service.toggle_availability(product_id)
            
            return success_response(
                data=ProductResponse.from_orm(product).dict(),
                message=f"Product availability {'enabled' if product.is_available else 'disabled'}"
            )
            
        except Exception as e:
            logger.error(f"Toggle product availability failed: {e}")
            raise
