"""
Products types and schemas.
"""
from pydantic import BaseModel, validator
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema."""
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    inventory_count: int = 0
    is_active: bool = True
    is_featured: bool = False


class ProductCreate(ProductBase):
    """Product creation schema."""
    
    @validator("name")
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Product name must be at least 2 characters long")
        if len(v.strip()) > 200:
            raise ValueError("Product name must be less than 200 characters")
        return v.strip()
    
    @validator("price")
    def validate_price(cls, v):
        if v < 0:
            raise ValueError("Price cannot be negative")
        if v > 1000000:
            raise ValueError("Price cannot exceed 1,000,000")
        return round(v, 2)
    
    @validator("inventory_count")
    def validate_inventory_count(cls, v):
        if v < 0:
            raise ValueError("Inventory count cannot be negative")
        return v
    
    @validator("description")
    def validate_description(cls, v):
        if v and len(v.strip()) > 1000:
            raise ValueError("Description must be less than 1000 characters")
        return v.strip() if v else None


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    inventory_count: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    
    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError("Product name must be at least 2 characters long")
            if len(v.strip()) > 200:
                raise ValueError("Product name must be less than 200 characters")
            return v.strip()
        return v
    
    @validator("price")
    def validate_price(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Price cannot be negative")
            if v > 1000000:
                raise ValueError("Price cannot exceed 1,000,000")
            return round(v, 2)
        return v
    
    @validator("inventory_count")
    def validate_inventory_count(cls, v):
        if v is not None and v < 0:
            raise ValueError("Inventory count cannot be negative")
        return v
    
    @validator("description")
    def validate_description(cls, v):
        if v is not None and len(v.strip()) > 1000:
            raise ValueError("Description must be less than 1000 characters")
        return v.strip() if v else None


class ProductResponse(ProductBase):
    """Product response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class ProductListResponse(BaseModel):
    """Product list response schema."""
    products: List[ProductResponse]
    total: int
    skip: int
    limit: int


class ProductSearchResponse(BaseModel):
    """Product search response schema."""
    products: List[ProductResponse]
    total: int
    search_term: str


class ProductStatsResponse(BaseModel):
    """Product statistics response schema."""
    product_id: int
    total_orders: int
    total_revenue: float
    average_rating: float
    view_count: int
    inventory_level: int
    last_order_date: Optional[datetime] = None


class ProductCategoryResponse(BaseModel):
    """Product category response schema."""
    categories: List[str]
    total: int


class ProductInventoryUpdate(BaseModel):
    """Product inventory update schema."""
    quantity: int
    
    @validator("quantity")
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


class ProductBulkUpdateRequest(BaseModel):
    """Product bulk update request schema."""
    product_updates: List[dict]


class ProductBulkUpdateResponse(BaseModel):
    """Product bulk update response schema."""
    processed: int
    successful: int
    failed: int
    errors: List[str]


class ProductFilterRequest(BaseModel):
    """Product filter request schema."""
    search: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    
    @validator("min_price", "max_price")
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("Price cannot be negative")
        return v
