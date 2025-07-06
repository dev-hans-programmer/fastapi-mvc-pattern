"""
Product schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, validator, HttpUrl

from app.common.schemas import TimestampMixin, IdMixin


class ProductCategoryBase(BaseModel):
    """Base product category schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=150)
    image_url: Optional[HttpUrl] = None
    parent_id: Optional[str] = None
    sort_order: int = Field(0, ge=0)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class ProductCategoryCreate(ProductCategoryBase):
    """Product category creation schema."""
    pass


class ProductCategoryUpdate(BaseModel):
    """Product category update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=1, max_length=150)
    image_url: Optional[HttpUrl] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ProductCategoryResponse(ProductCategoryBase, IdMixin, TimestampMixin):
    """Product category response schema."""
    products_count: Optional[int] = 0
    
    class Config:
        orm_mode = True


class ProductBrandBase(BaseModel):
    """Base product brand schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=150)
    logo_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class ProductBrandCreate(ProductBrandBase):
    """Product brand creation schema."""
    pass


class ProductBrandUpdate(BaseModel):
    """Product brand update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=1, max_length=150)
    logo_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ProductBrandResponse(ProductBrandBase, IdMixin, TimestampMixin):
    """Product brand response schema."""
    products_count: Optional[int] = 0
    
    class Config:
        orm_mode = True


class ProductVariantBase(BaseModel):
    """Base product variant schema."""
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    compare_price: Optional[Decimal] = Field(None, gt=0)
    inventory_quantity: int = Field(0, ge=0)
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions_length: Optional[Decimal] = Field(None, gt=0)
    dimensions_width: Optional[Decimal] = Field(None, gt=0)
    dimensions_height: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[HttpUrl] = None
    option1: Optional[str] = Field(None, max_length=100)
    option2: Optional[str] = Field(None, max_length=100)
    option3: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    """Product variant creation schema."""
    pass


class ProductVariantUpdate(BaseModel):
    """Product variant update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    compare_price: Optional[Decimal] = Field(None, gt=0)
    inventory_quantity: Optional[int] = Field(None, ge=0)
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions_length: Optional[Decimal] = Field(None, gt=0)
    dimensions_width: Optional[Decimal] = Field(None, gt=0)
    dimensions_height: Optional[Decimal] = Field(None, gt=0)
    image_url: Optional[HttpUrl] = None
    option1: Optional[str] = Field(None, max_length=100)
    option2: Optional[str] = Field(None, max_length=100)
    option3: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductVariantResponse(ProductVariantBase, IdMixin, TimestampMixin):
    """Product variant response schema."""
    product_id: str
    display_name: str
    
    class Config:
        orm_mode = True


class ProductAttributeBase(BaseModel):
    """Base product attribute schema."""
    name: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=500)
    type: str = Field("text", regex="^(text|number|boolean|date)$")
    display_order: int = Field(0, ge=0)
    is_searchable: bool = False
    is_comparable: bool = False


class ProductAttributeCreate(ProductAttributeBase):
    """Product attribute creation schema."""
    pass


class ProductAttributeUpdate(BaseModel):
    """Product attribute update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = Field(None, min_length=1, max_length=500)
    type: Optional[str] = Field(None, regex="^(text|number|boolean|date)$")
    display_order: Optional[int] = Field(None, ge=0)
    is_searchable: Optional[bool] = None
    is_comparable: Optional[bool] = None


class ProductAttributeResponse(ProductAttributeBase, IdMixin, TimestampMixin):
    """Product attribute response schema."""
    product_id: str
    
    class Config:
        orm_mode = True


class ProductReviewBase(BaseModel):
    """Base product review schema."""
    title: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1)
    rating: int = Field(..., ge=1, le=5)


class ProductReviewCreate(ProductReviewBase):
    """Product review creation schema."""
    pass


class ProductReviewUpdate(BaseModel):
    """Product review update schema."""
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)


class ProductReviewResponse(ProductReviewBase, IdMixin, TimestampMixin):
    """Product review response schema."""
    product_id: str
    user_id: str
    is_verified_purchase: bool
    is_approved: bool
    is_featured: bool
    helpful_count: int
    total_votes: int
    helpful_percentage: float
    
    class Config:
        orm_mode = True


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    slug: str = Field(..., min_length=1, max_length=250)
    sku: str = Field(..., min_length=1, max_length=100)
    price: Decimal = Field(..., gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    compare_price: Optional[Decimal] = Field(None, gt=0)
    track_inventory: bool = True
    inventory_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    allow_backorder: bool = False
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions_length: Optional[Decimal] = Field(None, gt=0)
    dimensions_width: Optional[Decimal] = Field(None, gt=0)
    dimensions_height: Optional[Decimal] = Field(None, gt=0)
    status: str = Field("active", regex="^(active|inactive|discontinued|out_of_stock)$")
    product_type: str = Field("physical", regex="^(physical|digital|service)$")
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = []
    image_url: Optional[HttpUrl] = None
    image_urls: Optional[List[HttpUrl]] = []
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    is_featured: bool = False
    is_digital: bool = False
    requires_shipping: bool = True
    is_taxable: bool = True
    
    @validator('compare_price')
    def validate_compare_price(cls, v, values):
        """Validate that compare price is higher than price."""
        if v is not None and 'price' in values and v <= values['price']:
            raise ValueError('Compare price must be higher than price')
        return v


class ProductCreate(ProductBase):
    """Product creation schema."""
    variants: Optional[List[ProductVariantCreate]] = []
    attributes: Optional[List[ProductAttributeCreate]] = []


class ProductUpdate(BaseModel):
    """Product update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    slug: Optional[str] = Field(None, min_length=1, max_length=250)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[Decimal] = Field(None, gt=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    compare_price: Optional[Decimal] = Field(None, gt=0)
    track_inventory: Optional[bool] = None
    inventory_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    allow_backorder: Optional[bool] = None
    weight: Optional[Decimal] = Field(None, gt=0)
    dimensions_length: Optional[Decimal] = Field(None, gt=0)
    dimensions_width: Optional[Decimal] = Field(None, gt=0)
    dimensions_height: Optional[Decimal] = Field(None, gt=0)
    status: Optional[str] = Field(None, regex="^(active|inactive|discontinued|out_of_stock)$")
    product_type: Optional[str] = Field(None, regex="^(physical|digital|service)$")
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    image_url: Optional[HttpUrl] = None
    image_urls: Optional[List[HttpUrl]] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    is_taxable: Optional[bool] = None


class ProductResponse(ProductBase, IdMixin, TimestampMixin):
    """Product response schema."""
    published_at: Optional[datetime] = None
    is_in_stock: bool
    is_low_stock: bool
    discount_percentage: float
    category: Optional[ProductCategoryResponse] = None
    brand: Optional[ProductBrandResponse] = None
    variants: List[ProductVariantResponse] = []
    attributes: List[ProductAttributeResponse] = []
    reviews_count: Optional[int] = 0
    average_rating: Optional[float] = 0.0
    
    class Config:
        orm_mode = True


class ProductListResponse(BaseModel):
    """Product list response schema."""
    id: str
    name: str
    slug: str
    sku: str
    price: Decimal
    compare_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    status: str
    is_featured: bool
    is_in_stock: bool
    discount_percentage: float
    category_name: Optional[str] = None
    brand_name: Optional[str] = None
    average_rating: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    created_at: datetime
    
    class Config:
        orm_mode = True


class ProductSearchFilters(BaseModel):
    """Product search filters schema."""
    name: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    status: Optional[str] = None
    product_type: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, gt=0)
    is_featured: Optional[bool] = None
    is_in_stock: Optional[bool] = None
    tags: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class ProductStatsResponse(BaseModel):
    """Product statistics response schema."""
    total_products: int
    active_products: int
    out_of_stock_products: int
    low_stock_products: int
    featured_products: int
    products_by_category: dict
    products_by_brand: dict
    average_price: float
    total_inventory_value: float


class BulkProductAction(BaseModel):
    """Bulk product action schema."""
    product_ids: List[str] = Field(..., min_items=1)
    action: str = Field(..., regex="^(activate|deactivate|feature|unfeature|delete)$")
    reason: Optional[str] = Field(None, max_length=500)


class InventoryAdjustment(BaseModel):
    """Inventory adjustment schema."""
    product_id: Optional[str] = None
    variant_id: Optional[str] = None
    quantity_change: int = Field(..., description="Positive for increase, negative for decrease")
    reason: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)
