"""
Order validation schemas
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.features.orders.types import OrderStatus, PaymentMethod


class AddressRequest(BaseModel):
    """
    Address validation schema
    """
    street: str = Field(..., min_length=1, max_length=200, description="Street address")
    apartment: Optional[str] = Field(None, max_length=50, description="Apartment/unit number")
    city: str = Field(..., min_length=1, max_length=100, description="City")
    state: str = Field(..., min_length=1, max_length=100, description="State/province")
    postal_code: str = Field(..., min_length=1, max_length=20, description="Postal/ZIP code")
    country: str = Field(..., min_length=1, max_length=100, description="Country")
    
    @validator("street", "city", "state", "country")
    def validate_required_fields(cls, v):
        """
        Validate required address fields
        """
        if not v.strip():
            raise ValueError("Address field cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "street": "123 Main Street",
                "apartment": "Apt 4B",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA"
            }
        }


class OrderItemRequest(BaseModel):
    """
    Order item validation schema
    """
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., min_length=1, description="Product name")
    quantity: int = Field(..., gt=0, description="Item quantity")
    price: float = Field(..., gt=0, description="Item price")
    product_sku: Optional[str] = Field(None, description="Product SKU")
    product_attributes: Optional[Dict[str, Any]] = Field(default={}, description="Product attributes")
    
    @validator("product_name")
    def validate_product_name(cls, v):
        """
        Validate product name
        """
        if not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": "product_123",
                "product_name": "Wireless Headphones",
                "quantity": 2,
                "price": 99.99,
                "product_sku": "WH-001",
                "product_attributes": {
                    "color": "Black",
                    "size": "Medium"
                }
            }
        }


class OrderCreateRequest(BaseModel):
    """
    Order creation request validation schema
    """
    items: List[OrderItemRequest] = Field(..., min_items=1, description="Order items")
    shipping_address: AddressRequest = Field(..., description="Shipping address")
    billing_address: Optional[AddressRequest] = Field(None, description="Billing address")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    notes: Optional[str] = Field(None, max_length=1000, description="Order notes")
    
    @validator("items")
    def validate_items(cls, v):
        """
        Validate order items
        """
        if not v:
            raise ValueError("Order must contain at least one item")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "product_id": "product_123",
                        "product_name": "Wireless Headphones",
                        "quantity": 1,
                        "price": 99.99,
                        "product_sku": "WH-001"
                    }
                ],
                "shipping_address": {
                    "street": "123 Main Street",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "payment_method": "credit_card",
                "notes": "Please deliver between 9 AM and 5 PM"
            }
        }


class OrderUpdateRequest(BaseModel):
    """
    Order update request validation schema
    """
    shipping_address: Optional[AddressRequest] = Field(None, description="Shipping address")
    billing_address: Optional[AddressRequest] = Field(None, description="Billing address")
    payment_method: Optional[PaymentMethod] = Field(None, description="Payment method")
    notes: Optional[str] = Field(None, max_length=1000, description="Order notes")
    
    class Config:
        schema_extra = {
            "example": {
                "shipping_address": {
                    "street": "456 Oak Avenue",
                    "city": "Boston",
                    "state": "MA",
                    "postal_code": "02101",
                    "country": "USA"
                },
                "notes": "Updated delivery instructions"
            }
        }


class OrderResponse(BaseModel):
    """
    Order response schema
    """
    id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    status: str = Field(..., description="Order status")
    subtotal: float = Field(..., description="Subtotal amount")
    tax_amount: float = Field(..., description="Tax amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    discount_amount: float = Field(default=0.0, description="Discount amount")
    total_amount: float = Field(..., description="Total amount")
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address")
    billing_address: Dict[str, Any] = Field(..., description="Billing address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    payment_status: str = Field(..., description="Payment status")
    tracking_number: Optional[str] = Field(None, description="Tracking number")
    notes: Optional[str] = Field(None, description="Order notes")
    is_active: bool = Field(..., description="Order active status")
    can_be_cancelled: bool = Field(..., description="Can be cancelled")
    can_be_shipped: bool = Field(..., description="Can be shipped")
    can_be_delivered: bool = Field(..., description="Can be delivered")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
    shipped_at: Optional[datetime] = Field(None, description="Shipping timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    
    @classmethod
    def from_orm(cls, order):
        """
        Create response from Order object
        """
        return cls(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            shipping_cost=order.shipping_cost,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            shipping_address=order.shipping_address or {},
            billing_address=order.billing_address or {},
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            tracking_number=order.tracking_number,
            notes=order.notes,
            is_active=order.is_active,
            can_be_cancelled=order.can_be_cancelled,
            can_be_shipped=order.can_be_shipped,
            can_be_delivered=order.can_be_delivered,
            created_at=order.created_at,
            updated_at=order.updated_at,
            confirmed_at=order.confirmed_at,
            shipped_at=order.shipped_at,
            delivered_at=order.delivered_at,
            cancelled_at=order.cancelled_at,
        )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "order_123",
                "user_id": "user_123",
                "status": "pending",
                "subtotal": 99.99,
                "tax_amount": 10.00,
                "shipping_cost": 5.99,
                "discount_amount": 0.0,
                "total_amount": 115.98,
                "shipping_address": {
                    "street": "123 Main Street",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "billing_address": {
                    "street": "123 Main Street",
                    "city": "New York",
                    "state": "NY",
                    "postal_code": "10001",
                    "country": "USA"
                },
                "payment_method": "credit_card",
                "payment_status": "pending",
                "tracking_number": None,
                "notes": "Please deliver between 9 AM and 5 PM",
                "is_active": True,
                "can_be_cancelled": True,
                "can_be_shipped": False,
                "can_be_delivered": False,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "confirmed_at": None,
                "shipped_at": None,
                "delivered_at": None,
                "cancelled_at": None
            }
        }


class OrderListResponse(BaseModel):
    """
    Order list response schema
    """
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
    skip: int = Field(..., description="Number of skipped orders")
    limit: int = Field(..., description="Maximum number of orders returned")
    
    class Config:
        schema_extra = {
            "example": {
                "orders": [
                    {
                        "id": "order_123",
                        "user_id": "user_123",
                        "status": "pending",
                        "subtotal": 99.99,
                        "tax_amount": 10.00,
                        "shipping_cost": 5.99,
                        "total_amount": 115.98,
                        "shipping_address": {},
                        "billing_address": {},
                        "payment_method": "credit_card",
                        "payment_status": "pending",
                        "is_active": True,
                        "can_be_cancelled": True,
                        "can_be_shipped": False,
                        "can_be_delivered": False,
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10
            }
        }


class OrderItemResponse(BaseModel):
    """
    Order item response schema
    """
    id: str = Field(..., description="Item ID")
    order_id: str = Field(..., description="Order ID")
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: Optional[str] = Field(None, description="Product SKU")
    quantity: int = Field(..., description="Item quantity")
    price: float = Field(..., description="Item price")
    total: float = Field(..., description="Item total")
    product_attributes: Dict[str, Any] = Field(default={}, description="Product attributes")
    
    @classmethod
    def from_orm(cls, item):
        """
        Create response from OrderItem object
        """
        return cls(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            product_name=item.product_name,
            product_sku=item.product_sku,
            quantity=item.quantity,
            price=item.price,
            total=item.total,
            product_attributes=item.product_attributes or {},
        )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "item_123",
                "order_id": "order_123",
                "product_id": "product_123",
                "product_name": "Wireless Headphones",
                "product_sku": "WH-001",
                "quantity": 1,
                "price": 99.99,
                "total": 99.99,
                "product_attributes": {
                    "color": "Black",
                    "size": "Medium"
                }
            }
        }


class OrderStatusUpdateRequest(BaseModel):
    """
    Order status update request schema
    """
    status: OrderStatus = Field(..., description="New order status")
    notes: Optional[str] = Field(None, max_length=1000, description="Status update notes")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "confirmed",
                "notes": "Order confirmed and payment processed"
            }
        }


class BulkOrderStatusUpdateRequest(BaseModel):
    """
    Bulk order status update request schema
    """
    order_ids: List[str] = Field(..., min_items=1, description="List of order IDs")
    status: OrderStatus = Field(..., description="New status for all orders")
    notes: Optional[str] = Field(None, max_length=1000, description="Status update notes")
    
    class Config:
        schema_extra = {
            "example": {
                "order_ids": ["order_123", "order_456"],
                "status": "confirmed",
                "notes": "Bulk confirmation of orders"
            }
        }


class OrderStatsResponse(BaseModel):
    """
    Order statistics response schema
    """
    order_id: str = Field(..., description="Order ID")
    status: str = Field(..., description="Order status")
    total_amount: float = Field(..., description="Total amount")
    item_count: int = Field(..., description="Number of items")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")
    days_since_created: int = Field(..., description="Days since order creation")
    is_active: bool = Field(..., description="Order active status")
    
    class Config:
        schema_extra = {
            "example": {
                "order_id": "order_123",
                "status": "pending",
                "total_amount": 115.98,
                "item_count": 2,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "days_since_created": 5,
                "is_active": True
            }
        }


class OrdersSummaryResponse(BaseModel):
    """
    Orders summary statistics response schema
    """
    total_orders: int = Field(..., description="Total number of orders")
    status_counts: Dict[str, int] = Field(..., description="Order counts by status")
    total_revenue: float = Field(..., description="Total revenue from delivered orders")
    pending_orders: int = Field(..., description="Number of pending orders")
    confirmed_orders: int = Field(..., description="Number of confirmed orders")
    shipped_orders: int = Field(..., description="Number of shipped orders")
    delivered_orders: int = Field(..., description="Number of delivered orders")
    cancelled_orders: int = Field(..., description="Number of cancelled orders")
    
    class Config:
        schema_extra = {
            "example": {
                "total_orders": 150,
                "status_counts": {
                    "pending": 25,
                    "confirmed": 30,
                    "shipped": 20,
                    "delivered": 60,
                    "cancelled": 15
                },
                "total_revenue": 12500.75,
                "pending_orders": 25,
                "confirmed_orders": 30,
                "shipped_orders": 20,
                "delivered_orders": 60,
                "cancelled_orders": 15
            }
        }


class MessageResponse(BaseModel):
    """
    Generic message response schema
    """
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Operation success status")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Operation completed successfully",
                "success": True
            }
        }
