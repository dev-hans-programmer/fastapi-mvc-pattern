"""
Products routes.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any

from app.features.products.controllers import ProductController
from app.features.products.services import ProductService
from app.features.products.repositories import ProductRepository
from app.features.products.types import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    ProductSearchResponse, ProductStatsResponse
)
from app.core.dependencies import get_db, get_current_user_id, get_optional_current_user_id
from app.core.database import Session

router = APIRouter()


def get_product_controller(db: Session = Depends(get_db)) -> ProductController:
    """Get product controller."""
    product_repository = ProductRepository(db)
    product_service = ProductService(product_repository)
    return ProductController(product_service)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user_id: int = Depends(get_current_user_id),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Create a new product."""
    return await product_controller.create_product(product_data)


@router.get("/", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of products to return"),
    search: Optional[str] = Query(None, description="Search term for name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Get list of products."""
    return await product_controller.get_products(
        skip=skip,
        limit=limit,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
    )


@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Search products."""
    return await product_controller.search_products(q, limit)


@router.get("/categories", response_model=List[str])
async def get_product_categories(
    product_controller: ProductController = Depends(get_product_controller),
):
    """Get all product categories."""
    return await product_controller.get_product_categories()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    product_controller: ProductController = Depends(get_product_controller),
):
    """Get product by ID."""
    return await product_controller.get_product(product_id)


@router.get("/{product_id}/stats", response_model=ProductStatsResponse)
async def get_product_stats(
    product_id: int,
    product_controller: ProductController = Depends(get_product_controller),
):
    """Get product statistics."""
    return await product_controller.get_product_stats(product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user_id: int = Depends(get_current_user_id),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Update product."""
    return await product_controller.update_product(product_id, product_data)


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user_id: int = Depends(get_current_user_id),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Delete product."""
    return await product_controller.delete_product(product_id)


@router.patch("/{product_id}/inventory")
async def update_product_inventory(
    product_id: int,
    quantity: int,
    current_user_id: int = Depends(get_current_user_id),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Update product inventory."""
    return await product_controller.update_product_inventory(product_id, quantity)


@router.post("/bulk-update")
async def bulk_update_products(
    product_updates: List[Dict[str, Any]],
    current_user_id: int = Depends(get_current_user_id),
    product_controller: ProductController = Depends(get_product_controller),
):
    """Bulk update products."""
    product_service = ProductService(ProductRepository(next(get_db())))
    return await product_service.bulk_update_products(product_updates)
