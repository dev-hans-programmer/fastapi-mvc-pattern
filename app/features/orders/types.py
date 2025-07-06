"""
Order types and models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.common.validators import BaseValidator


class Order(Base):
    """Order database model"""
    __tablename__ = "orders"
    
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Address information (stored as JSON)
    shipping_address: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    billing_address: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Payment information
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Order tracking
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes and metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base):
    """Order item database model"""
    __tablename__ = "order_items"
    
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Product information at time of order (snapshot)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"


class AddressBase(BaseModel):
    """Base address model"""
    name: str = Field(..., description="Full name")
    street_address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: str = Field(..., description="State/Province")
    postal_code: str = Field(..., description="Postal/ZIP code")
    country: str = Field(..., description="Country")
    phone: Optional[str] = Field(None, description="Phone number")
    
    @validator('name', 'street_address', 'city', 'state', 'country')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @validator('postal_code')
    def validate_postal_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Postal code cannot be empty")
        # Basic validation - could be more specific per country
        return v.strip()


class OrderItemBase(BaseModel):
    """Base order item model"""
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        if v > 1000:
            raise ValueError("Quantity cannot exceed 1000")
        return v


class OrderItemCreate(OrderItemBase):
    """Order item creation model"""
    pass


class OrderItemResponse(BaseModel):
    """Order item response model"""
    id: int = Field(..., description="Order item ID")
    product_id: int = Field(..., description="Product ID")
    quantity: int = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    total_price: float = Field(..., description="Total price")
    product_name: Optional[str] = Field(None, description="Product name")
    product_sku: Optional[str] = Field(None, description="Product SKU")
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order model"""
    shipping_address: AddressBase = Field(..., description="Shipping address")
    billing_address: Optional[AddressBase] = Field(None, description="Billing address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    notes: Optional[str] = Field(None, description="Order notes")
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 1000:
            raise ValueError("Notes cannot exceed 1000 characters")
        return v


class OrderCreate(OrderBase):
    """Order creation model"""
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order items")
    
    @validator('items')
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Order must contain at least one item")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 2
                    }
                ],
                "shipping_address": {
                    "name": "John Doe",
                    "street_address": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA",
                    "phone": "+1234567890"
                },
                "payment_method": "credit_card",
                "notes": "Please deliver after 6 PM"
            }
        }


class OrderUpdate(BaseModel):
    """Order update model"""
    shipping_address: Optional[AddressBase] = Field(None, description="Shipping address")
    billing_address: Optional[AddressBase] = Field(None, description="Billing address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    notes: Optional[str] = Field(None, description="Order notes")
    
    @validator('notes')
    def validate_notes(cls, v):
        if v and len(v) > 1000:
            raise ValueError("Notes cannot exceed 1000 characters")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "notes": "Updated delivery instructions",
                "payment_method": "paypal"
            }
        }


class OrderResponse(BaseModel):
    """Order response model"""
    id: int = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    user_id: int = Field(..., description="User ID")
    status: str = Field(..., description="Order status")
    subtotal: float = Field(..., description="Subtotal")
    tax_amount: float = Field(..., description="Tax amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    discount_amount: float = Field(..., description="Discount amount")
    total_amount: float = Field(..., description="Total amount")
    currency: str = Field(..., description="Currency")
    shipping_address: Optional[Dict] = Field(None, description="Shipping address")
    billing_address: Optional[Dict] = Field(None, description="Billing address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_status: str = Field(..., description="Payment status")
    payment_reference: Optional[str] = Field(None, description="Payment reference")
    tracking_number: Optional[str] = Field(None, description="Tracking number")
    shipped_at: Optional[datetime] = Field(None, description="Shipped timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    notes: Optional[str] = Field(None, description="Order notes")
    items: List[OrderItemResponse] = Field(default_factory=list, description="Order items")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "order_number": "ORD-20240101-A1B2",
                "user_id": 1,
                "status": "pending",
                "subtotal": 99.99,
                "tax_amount": 8.00,
                "shipping_cost": 9.99,
                "discount_amount": 0.00,
                "total_amount": 117.98,
                "currency": "USD",
                "shipping_address": {
                    "name": "John Doe",
                    "street_address": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "payment_method": "credit_card",
                "payment_status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }


class OrderListResponse(BaseModel):
    """Order list response model"""
    orders: list[OrderResponse] = Field(..., description="List of orders")
    total_count: int = Field(..., description="Total number of orders")
    
    class Config:
        schema_extra = {
            "example": {
                "orders": [
                    {
                        "id": 1,
                        "order_number": "ORD-20240101-A1B2",
                        "status": "pending",
                        "total_amount": 117.98,
                        "created_at": "2024-01-01T00:00:00"
                    }
                ],
                "total_count": 1
            }
        }


class OrderStatistics(BaseModel):
    """Order statistics model"""
    total_orders: int = Field(..., description="Total number of orders")
    status_counts: Dict[str, int] = Field(..., description="Orders count by status")
    revenue_statistics: Dict[str, Any] = Field(..., description="Revenue statistics")
    recent_orders_count: int = Field(..., description="Recent orders count")
    average_order_value: float = Field(..., description="Average order value")
    
    class Config:
        schema_extra = {
            "example": {
                "total_orders": 1000,
                "status_counts": {
                    "pending": 50,
                    "confirmed": 100,
                    "processing": 75,
                    "shipped": 200,
                    "delivered": 500,
                    "cancelled": 75
                },
                "revenue_statistics": {
                    "total_revenue": 50000.00,
                    "average_order_value": 125.50,
                    "monthly_revenue": {
                        "2024-01": 15000.00,
                        "2024-02": 18000.00,
                        "2024-03": 17000.00
                    }
                },
                "recent_orders_count": 150,
                "average_order_value": 125.50
            }
        }


class OrderStatusUpdate(BaseModel):
    """Order status update model"""
    status: str = Field(..., description="New order status")
    tracking_number: Optional[str] = Field(None, description="Tracking number")
    notes: Optional[str] = Field(None, description="Status update notes")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "shipped",
                "tracking_number": "TRK123456789",
                "notes": "Package shipped via FedEx"
            }
        }


class OrderSummary(BaseModel):
    """Order summary model"""
    order_id: int = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    status: str = Field(..., description="Order status")
    total_amount: float = Field(..., description="Total amount")
    item_count: int = Field(..., description="Number of items")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": 1,
                "order_number": "ORD-20240101-A1B2",
                "status": "pending",
                "total_amount": 117.98,
                "item_count": 3,
                "created_at": "2024-01-01T00:00:00"
            }
        }


class PaymentInfo(BaseModel):
    """Payment information model"""
    payment_method: str = Field(..., description="Payment method")
    payment_status: str = Field(..., description="Payment status")
    payment_reference: Optional[str] = Field(None, description="Payment reference")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency")
    processed_at: Optional[datetime] = Field(None, description="Payment processed timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "payment_method": "credit_card",
                "payment_status": "completed",
                "payment_reference": "PAY123456789",
                "amount": 117.98,
                "currency": "USD",
                "processed_at": "2024-01-01T12:00:00"
            }
        }
