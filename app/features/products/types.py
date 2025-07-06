"""
Product types and models
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.common.validators import BaseValidator


class Product(Base):
    """Product database model"""
    __tablename__ = "products"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 3), nullable=True)
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    material: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_digital: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_shipping: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"


class ProductBase(BaseModel):
    """Base product model"""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    sku: str = Field(..., min_length=1, max_length=100, description="Product SKU")
    price: float = Field(..., gt=0, description="Product price")
    cost_price: Optional[float] = Field(None, gt=0, description="Product cost price")
    stock_quantity: int = Field(0, ge=0, description="Stock quantity")
    min_stock_level: int = Field(0, ge=0, description="Minimum stock level")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    weight: Optional[float] = Field(None, gt=0, description="Product weight")
    dimensions: Optional[str] = Field(None, max_length=100, description="Product dimensions")
    color: Optional[str] = Field(None, max_length=50, description="Product color")
    size: Optional[str] = Field(None, max_length=50, description="Product size")
    material: Optional[str] = Field(None, max_length=100, description="Product material")
    
    @validator('name')
    def validate_name(cls, v):
        BaseValidator.validate_string_length(v, min_length=1, max_length=255, field_name="Product name")
        return v.strip()
    
    @validator('sku')
    def validate_sku(cls, v):
        import re
        v = v.strip().upper()
        if not re.match(r'^[A-Z0-9\-_]+$', v):
            raise ValueError("SKU can only contain letters, numbers, hyphens, and underscores")
        return v
    
    @validator('category', 'brand', 'color', 'size', 'material')
    def validate_optional_strings(cls, v):
        if v:
            return v.strip()
        return v


class ProductCreate(ProductBase):
    """Product creation model"""
    is_available: Optional[bool] = Field(True, description="Product availability")
    is_featured: Optional[bool] = Field(False, description="Featured status")
    is_digital: Optional[bool] = Field(False, description="Digital product flag")
    requires_shipping: Optional[bool] = Field(True, description="Requires shipping flag")
    tax_rate: Optional[float] = Field(None, ge=0, le=1, description="Tax rate (0.0-1.0)")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    image_url: Optional[str] = Field(None, description="Product image URL")
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if v:
            BaseValidator.validate_url(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "sku": "WBH-001",
                "price": 99.99,
                "cost_price": 45.00,
                "stock_quantity": 50,
                "min_stock_level": 10,
                "category": "Electronics",
                "brand": "TechBrand",
                "weight": 0.25,
                "color": "Black",
                "material": "Plastic",
                "is_available": True,
                "is_featured": False,
                "is_digital": False,
                "requires_shipping": True,
                "tax_rate": 0.08
            }
        }


class ProductUpdate(BaseModel):
    """Product update model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    sku: Optional[str] = Field(None, min_length=1, max_length=100, description="Product SKU")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    cost_price: Optional[float] = Field(None, gt=0, description="Product cost price")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    min_stock_level: Optional[int] = Field(None, ge=0, description="Minimum stock level")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    weight: Optional[float] = Field(None, gt=0, description="Product weight")
    dimensions: Optional[str] = Field(None, max_length=100, description="Product dimensions")
    color: Optional[str] = Field(None, max_length=50, description="Product color")
    size: Optional[str] = Field(None, max_length=50, description="Product size")
    material: Optional[str] = Field(None, max_length=100, description="Product material")
    is_available: Optional[bool] = Field(None, description="Product availability")
    is_featured: Optional[bool] = Field(None, description="Featured status")
    is_digital: Optional[bool] = Field(None, description="Digital product flag")
    requires_shipping: Optional[bool] = Field(None, description="Requires shipping flag")
    tax_rate: Optional[float] = Field(None, ge=0, le=1, description="Tax rate (0.0-1.0)")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    image_url: Optional[str] = Field(None, description="Product image URL")
    
    @validator('name')
    def validate_name(cls, v):
        if v:
            BaseValidator.validate_string_length(v, min_length=1, max_length=255, field_name="Product name")
            return v.strip()
        return v
    
    @validator('sku')
    def validate_sku(cls, v):
        if v:
            import re
            v = v.strip().upper()
            if not re.match(r'^[A-Z0-9\-_]+$', v):
                raise ValueError("SKU can only contain letters, numbers, hyphens, and underscores")
            return v
        return v
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if v:
            BaseValidator.validate_url(v)
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Product Name",
                "price": 109.99,
                "stock_quantity": 75,
                "is_featured": True
            }
        }


class ProductResponse(BaseModel):
    """Product response model"""
    id: int = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    sku: str = Field(..., description="Product SKU")
    price: float = Field(..., description="Product price")
    cost_price: Optional[float] = Field(None, description="Product cost price")
    stock_quantity: int = Field(..., description="Stock quantity")
    min_stock_level: int = Field(..., description="Minimum stock level")
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    weight: Optional[float] = Field(None, description="Product weight")
    dimensions: Optional[str] = Field(None, description="Product dimensions")
    color: Optional[str] = Field(None, description="Product color")
    size: Optional[str] = Field(None, description="Product size")
    material: Optional[str] = Field(None, description="Product material")
    is_available: bool = Field(..., description="Product availability")
    is_featured: bool = Field(..., description="Featured status")
    is_digital: bool = Field(..., description="Digital product flag")
    requires_shipping: bool = Field(..., description="Requires shipping flag")
    tax_rate: Optional[float] = Field(None, description="Tax rate")
    barcode: Optional[str] = Field(None, description="Product barcode")
    image_url: Optional[str] = Field(None, description="Product image URL")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "sku": "WBH-001",
                "price": 99.99,
                "cost_price": 45.00,
                "stock_quantity": 50,
                "min_stock_level": 10,
                "category": "Electronics",
                "brand": "TechBrand",
                "weight": 0.25,
                "color": "Black",
                "material": "Plastic",
                "is_available": True,
                "is_featured": False,
                "is_digital": False,
                "requires_shipping": True,
                "tax_rate": 0.08,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }


class ProductListResponse(BaseModel):
    """Product list response model"""
    products: list[ProductResponse] = Field(..., description="List of products")
    total_count: int = Field(..., description="Total number of products")
    
    class Config:
        schema_extra = {
            "example": {
                "products": [
                    {
                        "id": 1,
                        "name": "Wireless Bluetooth Headphones",
                        "sku": "WBH-001",
                        "price": 99.99,
                        "stock_quantity": 50,
                        "category": "Electronics",
                        "is_available": True,
                        "is_featured": False,
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T00:00:00"
                    }
                ],
                "total_count": 1
            }
        }


class ProductStatistics(BaseModel):
    """Product statistics model"""
    total_products: int = Field(..., description="Total number of products")
    available_products: int = Field(..., description="Number of available products")
    unavailable_products: int = Field(..., description="Number of unavailable products")
    featured_products: int = Field(..., description="Number of featured products")
    low_stock_count: int = Field(..., description="Number of low stock products")
    out_of_stock_count: int = Field(..., description="Number of out of stock products")
    categories: dict = Field(..., description="Products count by category")
    stock_statistics: dict = Field(..., description="Stock statistics")
    price_statistics: dict = Field(..., description="Price statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "total_products": 100,
                "available_products": 85,
                "unavailable_products": 15,
                "featured_products": 20,
                "low_stock_count": 5,
                "out_of_stock_count": 3,
                "categories": {
                    "Electronics": 50,
                    "Clothing": 30,
                    "Books": 20
                },
                "stock_statistics": {
                    "total_stock": 5000,
                    "average_stock": 50.0,
                    "minimum_stock": 0,
                    "maximum_stock": 500
                },
                "price_statistics": {
                    "average_price": 49.99,
                    "minimum_price": 9.99,
                    "maximum_price": 299.99
                }
            }
        }


class ProductInventory(BaseModel):
    """Product inventory model"""
    product_id: int = Field(..., description="Product ID")
    sku: str = Field(..., description="Product SKU")
    name: str = Field(..., description="Product name")
    current_stock: int = Field(..., description="Current stock quantity")
    min_stock_level: int = Field(..., description="Minimum stock level")
    stock_status: str = Field(..., description="Stock status")
    last_restock_date: Optional[datetime] = Field(None, description="Last restock date")
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "sku": "WBH-001",
                "name": "Wireless Bluetooth Headphones",
                "current_stock": 50,
                "min_stock_level": 10,
                "stock_status": "in_stock",
                "last_restock_date": "2024-01-01T00:00:00"
            }
        }


class ProductPrice(BaseModel):
    """Product price model"""
    product_id: int = Field(..., description="Product ID")
    current_price: float = Field(..., description="Current price")
    cost_price: Optional[float] = Field(None, description="Cost price")
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    price_history: list = Field(default_factory=list, description="Price change history")
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": 1,
                "current_price": 99.99,
                "cost_price": 45.00,
                "profit_margin": 55.0,
                "price_history": [
                    {
                        "price": 89.99,
                        "changed_at": "2023-12-01T00:00:00"
                    }
                ]
            }
        }
