"""
Product routes
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import get_current_user, get_current_active_user, get_current_admin_user, CommonQueryParams
from app.features.products.controllers import ProductController
from app.features.products.types import ProductCreate, ProductUpdate, ProductResponse, Product
from app.features.users.types import User
from app.common.decorators import rate_limit
from app.common.responses import success_response

logger = logging.getLogger(__name__)

products_router = APIRouter()


@products_router.post("/", response_model=Dict[str, Any])
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new product (Admin only)"""
    controller = ProductController(session)
    return await controller.create_product(product_data)


@products_router.get("/{product_id}", response_model=Dict[str, Any])
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get product by ID (Public)"""
    controller = ProductController(session)
    return await controller.get_product(product_id)


@products_router.get("/", response_model=Dict[str, Any])
async def get_products(
    params: CommonQueryParams = Depends(),
    session: AsyncSession = Depends(get_session)
):
    """Get all products (Public)"""
    controller = ProductController(session)
    return await controller.get_products(params)


@products_router.get("/paginated/list", response_model=Dict[str, Any])
async def get_products_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    session: AsyncSession = Depends(get_session)
):
    """Get products with pagination and filters (Public)"""
    controller = ProductController(session)
    return await controller.get_products_paginated(page, page_size, category, min_price, max_price, in_stock)


@products_router.put("/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Update product (Admin only)"""
    controller = ProductController(session)
    return await controller.update_product(product_id, product_data)


@products_router.delete("/{product_id}", response_model=Dict[str, Any])
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete product (Admin only)"""
    controller = ProductController(session)
    return await controller.delete_product(product_id)


@products_router.get("/sku/{sku}", response_model=Dict[str, Any])
async def get_product_by_sku(
    sku: str,
    session: AsyncSession = Depends(get_session)
):
    """Get product by SKU (Public)"""
    controller = ProductController(session)
    return await controller.get_product_by_sku(sku)


@products_router.get("/category/{category}", response_model=Dict[str, Any])
async def get_products_by_category(
    category: str,
    session: AsyncSession = Depends(get_session)
):
    """Get products by category (Public)"""
    controller = ProductController(session)
    return await controller.get_products_by_category(category)


@products_router.get("/search/query", response_model=Dict[str, Any])
async def search_products(
    search_term: str = Query(..., min_length=2, description="Search term"),
    skip: int = Query(0, ge=0, description="Skip items"),
    limit: int = Query(20, ge=1, le=100, description="Limit items"),
    session: AsyncSession = Depends(get_session)
):
    """Search products (Public)"""
    controller = ProductController(session)
    return await controller.search_products(search_term, skip, limit)


@products_router.patch("/{product_id}/stock", response_model=Dict[str, Any])
async def update_product_stock(
    product_id: int,
    quantity: int = Query(..., ge=0, description="New stock quantity"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Update product stock (Admin only)"""
    controller = ProductController(session)
    return await controller.update_product_stock(product_id, quantity)


@products_router.get("/inventory/low-stock", response_model=Dict[str, Any])
async def get_low_stock_products(
    threshold: int = Query(10, ge=0, description="Stock threshold"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get products with low stock (Admin only)"""
    controller = ProductController(session)
    return await controller.get_low_stock_products(threshold)


@products_router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_product_statistics(
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Get product statistics (Admin only)"""
    controller = ProductController(session)
    return await controller.get_product_statistics()


@products_router.post("/bulk/create", response_model=Dict[str, Any])
@rate_limit(max_calls=5, window=300)  # 5 bulk operations per 5 minutes
async def bulk_create_products(
    products_data: List[ProductCreate],
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Bulk create products (Admin only)"""
    controller = ProductController(session)
    return await controller.bulk_create_products(products_data)


@products_router.put("/bulk/update", response_model=Dict[str, Any])
@rate_limit(max_calls=5, window=300)  # 5 bulk operations per 5 minutes
async def bulk_update_products(
    updates: List[Dict[str, Any]],
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Bulk update products (Admin only)"""
    controller = ProductController(session)
    return await controller.bulk_update_products(updates)


@products_router.get("/featured/list", response_model=Dict[str, Any])
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50, description="Number of featured products"),
    session: AsyncSession = Depends(get_session)
):
    """Get featured products (Public)"""
    controller = ProductController(session)
    return await controller.get_featured_products(limit)


@products_router.patch("/{product_id}/toggle-availability", response_model=Dict[str, Any])
async def toggle_product_availability(
    product_id: int,
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Toggle product availability (Admin only)"""
    controller = ProductController(session)
    return await controller.toggle_product_availability(product_id)


@products_router.patch("/{product_id}/featured", response_model=Dict[str, Any])
async def set_product_featured(
    product_id: int,
    is_featured: bool = Query(..., description="Featured status"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Set product featured status (Admin only)"""
    from app.features.products.services import ProductService
    from app.features.products.repositories import ProductRepository
    
    product_repository = ProductRepository(session)
    product_service = ProductService(product_repository)
    
    product = await product_service.set_featured(product_id, is_featured)
    
    return success_response(
        data=ProductResponse.from_orm(product).dict(),
        message=f"Product {'featured' if is_featured else 'unfeatured'} successfully"
    )


@products_router.patch("/{product_id}/price", response_model=Dict[str, Any])
async def update_product_price(
    product_id: int,
    new_price: float = Query(..., gt=0, description="New price"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Update product price (Admin only)"""
    from app.features.products.services import ProductService
    from app.features.products.repositories import ProductRepository
    
    product_repository = ProductRepository(session)
    product_service = ProductService(product_repository)
    
    product = await product_service.update_price(product_id, new_price)
    
    return success_response(
        data=ProductResponse.from_orm(product).dict(),
        message="Product price updated successfully"
    )


@products_router.get("/{product_id}/related", response_model=Dict[str, Any])
async def get_related_products(
    product_id: int,
    limit: int = Query(5, ge=1, le=20, description="Number of related products"),
    session: AsyncSession = Depends(get_session)
):
    """Get related products (Public)"""
    from app.features.products.services import ProductService
    from app.features.products.repositories import ProductRepository
    
    product_repository = ProductRepository(session)
    product_service = ProductService(product_repository)
    
    products = await product_service.get_related_products(product_id, limit)
    product_responses = [ProductResponse.from_orm(product).dict() for product in products]
    
    return success_response(
        data=product_responses,
        message="Related products retrieved successfully"
    )


@products_router.get("/price-range/filter", response_model=Dict[str, Any])
async def get_products_by_price_range(
    min_price: float = Query(..., ge=0, description="Minimum price"),
    max_price: float = Query(..., gt=0, description="Maximum price"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products"),
    session: AsyncSession = Depends(get_session)
):
    """Get products by price range (Public)"""
    if min_price >= max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum price must be less than maximum price"
        )
    
    from app.features.products.services import ProductService
    from app.features.products.repositories import ProductRepository
    
    product_repository = ProductRepository(session)
    product_service = ProductService(product_repository)
    
    products = await product_service.get_products_by_price_range(min_price, max_price, limit)
    product_responses = [ProductResponse.from_orm(product).dict() for product in products]
    
    return success_response(
        data=product_responses,
        message=f"Products in price range ${min_price}-${max_price} retrieved successfully"
    )


@products_router.get("/search/advanced", response_model=Dict[str, Any])
async def advanced_product_search(
    search_term: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    skip: int = Query(0, ge=0, description="Skip items"),
    limit: int = Query(20, ge=1, le=100, description="Limit items"),
    session: AsyncSession = Depends(get_session)
):
    """Advanced product search with multiple filters (Public)"""
    from app.features.products.services import ProductService
    from app.features.products.repositories import ProductRepository
    
    product_repository = ProductRepository(session)
    product_service = ProductService(product_repository)
    
    products = await product_service.search_products_advanced(
        search_term=search_term,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        is_featured=is_featured,
        skip=skip,
        limit=limit
    )
    
    product_responses = [ProductResponse.from_orm(product).dict() for product in products]
    
    return success_response(
        data=product_responses,
        message="Advanced product search completed"
    )


@products_router.get("/export/data", response_model=Dict[str, Any])
async def export_products(
    format: str = Query("csv", regex="^(csv|json)$", description="Export format"),
    current_user: User = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_session)
):
    """Export products (Admin only)"""
    controller = ProductController(session)
    return await controller.export_products(format)


@products_router.get("/categories/list", response_model=Dict[str, Any])
async def get_product_categories(
    session: AsyncSession = Depends(get_session)
):
    """Get all product categories (Public)"""
    from app.features.products.repositories import ProductRepository
    
    product_repository = ProductRepository(session)
    categories = await product_repository.get_product_categories()
    
    return success_response(
        data=categories,
        message="Product categories retrieved successfully"
    )
