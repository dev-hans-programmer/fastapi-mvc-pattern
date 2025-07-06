"""
Orders types and schemas.
"""
from pydantic import BaseModel, validator
from typing import Optional, List, Any
from datetime import datetime


class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: int
    quantity: int
    
    @validator("quantity")
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        if v > 1000:
            raise ValueError("Quantity cannot exceed 1000")
        return v


class OrderItemCreate(OrderItemBase):
    """Order item creation schema."""
    pass


class OrderItemResponse(OrderItemBase):
    """Order item response schema."""
    id: int
    order_id: int
    unit_price: float
    total_price: float
    
    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    """Base order schema."""
    shipping_address: str
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    """Order creation schema."""
    items: List[OrderItemCreate]
    
    @validator("items")
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must have at least one item")
        if len(v) > 100:
            raise ValueError("Order cannot have more than 100 items")
        return v
    
    @validator("shipping_address")
    def validate_shipping_address(cls, v):
        if len(v.strip()) < 10:
            raise ValueError("Shipping address must be at least 10 characters long")
        if len(v.strip()) > 500:
            raise ValueError("Shipping address must be less than 500 characters")
        return v.strip()
    
    @validator("notes")
    def validate_notes(cls, v):
        if v and len(v.strip()) > 1000:
            raise ValueError("Notes must be less than 1000 characters")
        return v.strip() if v else None


class OrderUpdate(BaseModel):
    """Order update schema."""
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    
    @validator("shipping_address")
    def validate_shipping_address(cls, v):
        if v is not None:
            if len(v.strip()) < 10:
                raise ValueError("Shipping address must be at least 10 characters long")
            if len(v.strip()) > 500:
                raise ValueError("Shipping address must be less than 500 characters")
            return v.strip()
        return v
    
    @validator("notes")
    def validate_notes(cls, v):
        if v is not None and len(v.strip()) > 1000:
            raise ValueError("Notes must be less than 1000 characters")
        return v.strip() if v else None
    
    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v


class OrderResponse(OrderBase):
    """Order response schema."""
    id: int
    user_id: int
    status: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    
    class Config:
        orm_mode = True


class OrderListResponse(BaseModel):
    """Order list response schema."""
    orders: List[OrderResponse]
    total: int
    skip: int
    limit: int


class OrderStatsResponse(BaseModel):
    """Order statistics response schema."""
    order_id: int
    total_amount: float
    item_count: int
    processing_time: float
    shipping_cost: float
    tax_amount: float
    discount_amount: float


class OrderSummaryResponse(BaseModel):
    """Order summary response schema."""
    total_orders: int
    total_spent: float
    status_counts: dict
    average_order_value: float


class OrderPaymentRequest(BaseModel):
    """Order payment request schema."""
    method: str
    card_number: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None
    
    @validator("method")
    def validate_method(cls, v):
        valid_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        if v not in valid_methods:
            raise ValueError(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
        return v


class OrderPaymentResponse(BaseModel):
    """Order payment response schema."""
    payment_id: str
    status: str
    amount: float
    method: str
    processed_at: str


class OrderStatusUpdate(BaseModel):
    """Order status update schema."""
    status: str
    
    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v


class OrderFilterRequest(BaseModel):
    """Order filter request schema."""
    status: Optional[str] = None
    user_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    
    @validator("min_amount", "max_amount")
    def validate_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError("Amount cannot be negative")
        return v
    
    @validator("start_date", "end_date")
    def validate_dates(cls, v):
        if v is not None and v > datetime.utcnow():
            raise ValueError("Date cannot be in the future")
        return v
