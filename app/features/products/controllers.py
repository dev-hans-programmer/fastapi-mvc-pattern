"""
Products controllers.
"""
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
import logging

from app.features.products.services import ProductService
from app.features.products.types import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductSearchResponse, ProductStatsResponse
)
from app.features.products.validation import validate_product_create, validate_product_update
from app.core.exceptions import NotFoundException, ValidationException
from app.core.thread_pool import run_in_thread

logger = logging.getLogger(__name__)


class ProductController:
    """Product controller."""
    
    def __init__(self, product_service: ProductService):
        self.product_service = product_service
    
    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Create a new product."""
        try:
            # Validate request
            validate_product_create(product_data)
            
            # Create product
            product = await self.product_service.create_product(product_data)
            
            logger.info(f"Product created successfully: {product.name}")
            
            return ProductResponse.from_orm(product)
        
        except ValidationException as e:
            logger.error(f"Validation error in create_product: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in create_product: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product",
            )
    
    async def get_product(self, product_id: int) -> ProductResponse:
        """Get product by ID."""
        try:
            product = await self.product_service.get_product_by_id(product_id)
            
            if not product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            return ProductResponse.from_orm(product)
        
        except NotFoundException as e:
            logger.error(f"Product not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_product: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get product",
            )
    
    async def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        is_active: Optional[bool] = None,
    ) -> ProductListResponse:
        """Get list of products."""
        try:
            products, total = await self.product_service.get_products(
                skip=skip,
                limit=limit,
                search=search,
                category=category,
                min_price=min_price,
                max_price=max_price,
                is_active=is_active,
            )
            
            product_responses = [ProductResponse.from_orm(product) for product in products]
            
            return ProductListResponse(
                products=product_responses,
                total=total,
                skip=skip,
                limit=limit,
            )
        
        except Exception as e:
            logger.error(f"Error in get_products: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get products",
            )
    
    async def update_product(self, product_id: int, product_data: ProductUpdate) -> ProductResponse:
        """Update product."""
        try:
            # Validate request
            validate_product_update(product_data)
            
            # Update product
            product = await self.product_service.update_product(product_id, product_data)
            
            if not product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            logger.info(f"Product updated successfully: {product.name}")
            
            return ProductResponse.from_orm(product)
        
        except NotFoundException as e:
            logger.error(f"Product not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except ValidationException as e:
            logger.error(f"Validation error in update_product: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in update_product: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product",
            )
    
    async def delete_product(self, product_id: int) -> Dict[str, str]:
        """Delete product."""
        try:
            success = await self.product_service.delete_product(product_id)
            
            if not success:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            logger.info(f"Product deleted successfully: {product_id}")
            
            return {"message": "Product deleted successfully"}
        
        except NotFoundException as e:
            logger.error(f"Product not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in delete_product: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product",
            )
    
    async def search_products(self, query: str, limit: int = 10) -> ProductSearchResponse:
        """Search products."""
        try:
            products = await self.product_service.search_products(query, limit)
            
            product_responses = [ProductResponse.from_orm(product) for product in products]
            
            return ProductSearchResponse(
                products=product_responses,
                total=len(product_responses),
                search_term=query,
            )
        
        except Exception as e:
            logger.error(f"Error in search_products: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search products",
            )
    
    async def get_product_categories(self) -> List[str]:
        """Get all product categories."""
        try:
            categories = await self.product_service.get_product_categories()
            return categories
        
        except Exception as e:
            logger.error(f"Error in get_product_categories: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get product categories",
            )
    
    @run_in_thread
    def get_product_stats(self, product_id: int) -> ProductStatsResponse:
        """Get product statistics (CPU-intensive operation)."""
        try:
            stats = self.product_service.calculate_product_stats(product_id)
            
            if not stats:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            return stats
        
        except NotFoundException as e:
            logger.error(f"Product not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in get_product_stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get product statistics",
            )
    
    async def update_product_inventory(self, product_id: int, quantity: int) -> Dict[str, Any]:
        """Update product inventory."""
        try:
            success = await self.product_service.update_product_inventory(product_id, quantity)
            
            if not success:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            logger.info(f"Product inventory updated: {product_id}, quantity: {quantity}")
            
            return {
                "message": "Product inventory updated successfully",
                "product_id": product_id,
                "new_quantity": quantity,
            }
        
        except NotFoundException as e:
            logger.error(f"Product not found: {e.message}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=e.message,
            )
        except Exception as e:
            logger.error(f"Error in update_product_inventory: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product inventory",
            )
