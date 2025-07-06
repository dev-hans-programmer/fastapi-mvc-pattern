"""
Products validation utilities.
"""
import re
from typing import List
from app.features.products.types import ProductCreate, ProductUpdate
from app.core.exceptions import ValidationException


def validate_product_name(name: str) -> List[str]:
    """Validate product name."""
    errors = []
    
    if not name or len(name.strip()) < 2:
        errors.append("Product name must be at least 2 characters long")
    
    if len(name.strip()) > 200:
        errors.append("Product name must be less than 200 characters")
    
    # Check for invalid characters
    if re.search(r'[<>"\']', name):
        errors.append("Product name contains invalid characters")
    
    return errors


def validate_product_price(price: float) -> List[str]:
    """Validate product price."""
    errors = []
    
    if price < 0:
        errors.append("Price cannot be negative")
    
    if price > 1000000:
        errors.append("Price cannot exceed 1,000,000")
    
    # Check for reasonable decimal places
    if len(str(price).split('.')[-1]) > 2:
        errors.append("Price cannot have more than 2 decimal places")
    
    return errors


def validate_product_description(description: str) -> List[str]:
    """Validate product description."""
    errors = []
    
    if description and len(description.strip()) > 1000:
        errors.append("Description must be less than 1000 characters")
    
    # Check for invalid characters
    if description and re.search(r'[<>]', description):
        errors.append("Description contains invalid characters")
    
    return errors


def validate_product_category(category: str) -> List[str]:
    """Validate product category."""
    errors = []
    
    if category and len(category.strip()) < 2:
        errors.append("Category must be at least 2 characters long")
    
    if category and len(category.strip()) > 50:
        errors.append("Category must be less than 50 characters")
    
    # Check for invalid characters
    if category and re.search(r'[<>"\']', category):
        errors.append("Category contains invalid characters")
    
    return errors


def validate_inventory_count(count: int) -> List[str]:
    """Validate inventory count."""
    errors = []
    
    if count < 0:
        errors.append("Inventory count cannot be negative")
    
    if count > 1000000:
        errors.append("Inventory count cannot exceed 1,000,000")
    
    return errors


def validate_product_create(product_data: ProductCreate) -> None:
    """Validate product creation data."""
    errors = []
    
    # Validate name
    name_errors = validate_product_name(product_data.name)
    errors.extend(name_errors)
    
    # Validate price
    price_errors = validate_product_price(product_data.price)
    errors.extend(price_errors)
    
    # Validate description
    if product_data.description:
        description_errors = validate_product_description(product_data.description)
        errors.extend(description_errors)
    
    # Validate category
    if product_data.category:
        category_errors = validate_product_category(product_data.category)
        errors.extend(category_errors)
    
    # Validate inventory count
    inventory_errors = validate_inventory_count(product_data.inventory_count)
    errors.extend(inventory_errors)
    
    if errors:
        raise ValidationException(
            message="Product creation validation failed",
            details={"errors": errors}
        )


def validate_product_update(product_data: ProductUpdate) -> None:
    """Validate product update data."""
    errors = []
    
    # Validate name if provided
    if product_data.name:
        name_errors = validate_product_name(product_data.name)
        errors.extend(name_errors)
    
    # Validate price if provided
    if product_data.price is not None:
        price_errors = validate_product_price(product_data.price)
        errors.extend(price_errors)
    
    # Validate description if provided
    if product_data.description:
        description_errors = validate_product_description(product_data.description)
        errors.extend(description_errors)
    
    # Validate category if provided
    if product_data.category:
        category_errors = validate_product_category(product_data.category)
        errors.extend(category_errors)
    
    # Validate inventory count if provided
    if product_data.inventory_count is not None:
        inventory_errors = validate_inventory_count(product_data.inventory_count)
        errors.extend(inventory_errors)
    
    if errors:
        raise ValidationException(
            message="Product update validation failed",
            details={"errors": errors}
        )


def sanitize_product_input(input_string: str) -> str:
    """Sanitize product input."""
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', input_string)
    return sanitized.strip()


def validate_product_id(product_id: int) -> None:
    """Validate product ID."""
    if product_id <= 0:
        raise ValidationException("Invalid product ID")


def validate_search_query(query: str) -> None:
    """Validate search query."""
    errors = []
    
    if not query or len(query.strip()) < 2:
        errors.append("Search query must be at least 2 characters long")
    
    if len(query.strip()) > 100:
        errors.append("Search query must be less than 100 characters")
    
    if errors:
        raise ValidationException(
            message="Search query validation failed",
            details={"errors": errors}
        )


def validate_price_range(min_price: float, max_price: float) -> None:
    """Validate price range."""
    errors = []
    
    if min_price < 0:
        errors.append("Minimum price cannot be negative")
    
    if max_price < 0:
        errors.append("Maximum price cannot be negative")
    
    if min_price > max_price:
        errors.append("Minimum price cannot be greater than maximum price")
    
    if errors:
        raise ValidationException(
            message="Price range validation failed",
            details={"errors": errors}
        )
