"""
Orders validation utilities.
"""
import re
from typing import List
from datetime import datetime
from app.features.orders.types import OrderCreate, OrderUpdate, OrderItemCreate
from app.core.exceptions import ValidationException


def validate_order_items(items: List[OrderItemCreate]) -> List[str]:
    """Validate order items."""
    errors = []
    
    if not items:
        errors.append("Order must have at least one item")
        return errors
    
    if len(items) > 100:
        errors.append("Order cannot have more than 100 items")
    
    # Check for duplicate products
    product_ids = [item.product_id for item in items]
    if len(product_ids) != len(set(product_ids)):
        errors.append("Duplicate products are not allowed")
    
    # Validate each item
    for i, item in enumerate(items):
        if item.product_id <= 0:
            errors.append(f"Item {i+1}: Invalid product ID")
        
        if item.quantity <= 0:
            errors.append(f"Item {i+1}: Quantity must be positive")
        
        if item.quantity > 1000:
            errors.append(f"Item {i+1}: Quantity cannot exceed 1000")
    
    return errors


def validate_shipping_address(address: str) -> List[str]:
    """Validate shipping address."""
    errors = []
    
    if not address or len(address.strip()) < 10:
        errors.append("Shipping address must be at least 10 characters long")
    
    if len(address.strip()) > 500:
        errors.append("Shipping address must be less than 500 characters")
    
    # Check for minimum required components
    address_lower = address.lower()
    if not any(keyword in address_lower for keyword in ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'lane', 'ln']):
        errors.append("Shipping address should include street information")
    
    # Check for invalid characters
    if re.search(r'[<>"\']', address):
        errors.append("Shipping address contains invalid characters")
    
    return errors


def validate_order_notes(notes: str) -> List[str]:
    """Validate order notes."""
    errors = []
    
    if notes and len(notes.strip()) > 1000:
        errors.append("Notes must be less than 1000 characters")
    
    # Check for invalid characters
    if notes and re.search(r'[<>]', notes):
        errors.append("Notes contain invalid characters")
    
    return errors


def validate_order_status(status: str) -> List[str]:
    """Validate order status."""
    errors = []
    
    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    return errors


def validate_order_create(order_data: OrderCreate) -> None:
    """Validate order creation data."""
    errors = []
    
    # Validate items
    items_errors = validate_order_items(order_data.items)
    errors.extend(items_errors)
    
    # Validate shipping address
    address_errors = validate_shipping_address(order_data.shipping_address)
    errors.extend(address_errors)
    
    # Validate notes
    if order_data.notes:
        notes_errors = validate_order_notes(order_data.notes)
        errors.extend(notes_errors)
    
    if errors:
        raise ValidationException(
            message="Order creation validation failed",
            details={"errors": errors}
        )


def validate_order_update(order_data: OrderUpdate) -> None:
    """Validate order update data."""
    errors = []
    
    # Validate shipping address if provided
    if order_data.shipping_address:
        address_errors = validate_shipping_address(order_data.shipping_address)
        errors.extend(address_errors)
    
    # Validate notes if provided
    if order_data.notes:
        notes_errors = validate_order_notes(order_data.notes)
        errors.extend(notes_errors)
    
    # Validate status if provided
    if order_data.status:
        status_errors = validate_order_status(order_data.status)
        errors.extend(status_errors)
    
    if errors:
        raise ValidationException(
            message="Order update validation failed",
            details={"errors": errors}
        )


def validate_order_id(order_id: int) -> None:
    """Validate order ID."""
    if order_id <= 0:
        raise ValidationException("Invalid order ID")


def validate_payment_method(method: str) -> List[str]:
    """Validate payment method."""
    errors = []
    
    valid_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
    if method not in valid_methods:
        errors.append(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
    
    return errors


def validate_payment_data(payment_data: dict) -> None:
    """Validate payment data."""
    errors = []
    
    method = payment_data.get("method")
    if not method:
        errors.append("Payment method is required")
    else:
        method_errors = validate_payment_method(method)
        errors.extend(method_errors)
    
    # Additional validation for credit card
    if method == "credit_card":
        card_number = payment_data.get("card_number")
        if not card_number or len(card_number.replace(" ", "")) < 13:
            errors.append("Valid card number is required")
        
        card_expiry = payment_data.get("card_expiry")
        if not card_expiry or not re.match(r'^\d{2}/\d{2}$', card_expiry):
            errors.append("Valid card expiry (MM/YY) is required")
        
        card_cvv = payment_data.get("card_cvv")
        if not card_cvv or not re.match(r'^\d{3,4}$', card_cvv):
            errors.append("Valid CVV is required")
    
    if errors:
        raise ValidationException(
            message="Payment data validation failed",
            details={"errors": errors}
        )


def sanitize_order_input(input_string: str) -> str:
    """Sanitize order input."""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    return sanitized.strip()


def validate_order_amount(amount: float) -> List[str]:
    """Validate order amount."""
    errors = []
    
    if amount < 0:
        errors.append("Order amount cannot be negative")
    
    if amount > 1000000:
        errors.append("Order amount cannot exceed 1,000,000")
    
    return errors


def validate_date_range(start_date: datetime, end_date: datetime) -> List[str]:
    """Validate date range."""
    errors = []
    
    if start_date > end_date:
        errors.append("Start date cannot be after end date")
    
    if start_date > datetime.utcnow():
        errors.append("Start date cannot be in the future")
    
    if end_date > datetime.utcnow():
        errors.append("End date cannot be in the future")
    
    return errors
