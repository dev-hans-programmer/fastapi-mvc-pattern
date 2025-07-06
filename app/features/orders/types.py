"""
Order types and data models
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal


class OrderStatus(str, Enum):
    """
    Order status enumeration
    """
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """
    Payment status enumeration
    """
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """
    Payment method enumeration
    """
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cash_on_delivery"


@dataclass
class Order:
    """
    Order data model
    """
    id: str
    user_id: str
    status: str = OrderStatus.PENDING
    subtotal: float = 0.0
    tax_amount: float = 0.0
    shipping_cost: float = 0.0
    discount_amount: float = 0.0
    total_amount: float = 0.0
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: Optional[str] = None
    payment_status: str = PaymentStatus.PENDING
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.shipping_address is None:
            self.shipping_address = {}
        if self.billing_address is None:
            self.billing_address = {}
    
    @property
    def is_active(self) -> bool:
        """
        Check if order is active (not cancelled or delivered)
        """
        return self.status not in [OrderStatus.CANCELLED, OrderStatus.DELIVERED, OrderStatus.REFUNDED]
    
    @property
    def can_be_cancelled(self) -> bool:
        """
        Check if order can be cancelled
        """
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    @property
    def can_be_shipped(self) -> bool:
        """
        Check if order can be shipped
        """
        return self.status == OrderStatus.CONFIRMED
    
    @property
    def can_be_delivered(self) -> bool:
        """
        Check if order can be marked as delivered
        """
        return self.status == OrderStatus.SHIPPED
    
    def calculate_total(self) -> float:
        """
        Calculate total order amount
        """
        return self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert order to dictionary
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "status": self.status,
            "subtotal": self.subtotal,
            "tax_amount": self.tax_amount,
            "shipping_cost": self.shipping_cost,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "shipping_address": self.shipping_address,
            "billing_address": self.billing_address,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "tracking_number": self.tracking_number,
            "notes": self.notes,
            "is_active": self.is_active,
            "can_be_cancelled": self.can_be_cancelled,
            "can_be_shipped": self.can_be_shipped,
            "can_be_delivered": self.can_be_delivered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }


@dataclass
class OrderItem:
    """
    Order item data model
    """
    id: str
    order_id: str
    product_id: str
    product_name: str
    quantity: int
    price: float
    total: float
    product_sku: Optional[str] = None
    product_attributes: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.product_attributes is None:
            self.product_attributes = {}
    
    def calculate_total(self) -> float:
        """
        Calculate item total
        """
        return self.price * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert item to dictionary
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "quantity": self.quantity,
            "price": self.price,
            "total": self.total,
            "product_attributes": self.product_attributes,
        }


@dataclass
class OrderStatusHistory:
    """
    Order status history data model
    """
    id: str
    order_id: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert status history to dictionary
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }


@dataclass
class OrderPayment:
    """
    Order payment data model
    """
    id: str
    order_id: str
    amount: float
    payment_method: str
    payment_status: str = PaymentStatus.PENDING
    transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.gateway_response is None:
            self.gateway_response = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert payment to dictionary
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": self.amount,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "transaction_id": self.transaction_id,
            "gateway_response": self.gateway_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


@dataclass
class OrderShipment:
    """
    Order shipment data model
    """
    id: str
    order_id: str
    tracking_number: str
    carrier: str
    shipped_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert shipment to dictionary
        """
        return {
            "id": self.id,
            "order_id": self.order_id,
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }


@dataclass
class Address:
    """
    Address data model
    """
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    apartment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert address to dictionary
        """
        return {
            "street": self.street,
            "apartment": self.apartment,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }
    
    def __str__(self) -> str:
        """
        Format address as string
        """
        parts = [self.street]
        if self.apartment:
            parts.append(f"Apt {self.apartment}")
        parts.extend([self.city, self.state, self.postal_code, self.country])
        return ", ".join(parts)


# Order constants
class OrderFields:
    """
    Order field constants for queries and validation
    """
    ID = "id"
    USER_ID = "user_id"
    STATUS = "status"
    TOTAL_AMOUNT = "total_amount"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


# Status transition rules
ORDER_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
    OrderStatus.CANCELLED: [],
    OrderStatus.REFUNDED: [],
}


def can_transition_status(current_status: str, new_status: str) -> bool:
    """
    Check if status transition is allowed
    """
    return new_status in ORDER_STATUS_TRANSITIONS.get(current_status, [])
