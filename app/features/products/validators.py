"""
Product validators
"""
import re
from typing import Dict, List, Optional, Any
from decimal import Decimal

from app.common.validators import BaseValidator, CustomValidationError
from app.core.exceptions import ValidationError


class ProductValidator(BaseValidator):
    """Product-specific validators"""
    
    @staticmethod
    def validate_product_creation_data(
        name: str,
        sku: str,
        price: float,
        stock_quantity: int = 0,
        category: Optional[str] = None,
        brand: Optional[str] = None
    ) -> None:
        """Validate product creation data"""
        # Validate name
        ProductValidator.validate_product_name(name)
        
        # Validate SKU
        ProductValidator.validate_sku(sku)
        
        # Validate price
        ProductValidator.validate_price(price)
        
        # Validate stock quantity
        ProductValidator.validate_stock_quantity(stock_quantity)
        
        # Validate optional fields
        if category:
            ProductValidator.validate_category(category)
        
        if brand:
            ProductValidator.validate_brand(brand)
    
    @staticmethod
    def validate_product_name(name: str) -> None:
        """Validate product name"""
        if not name or not name.strip():
            raise ValidationError("Product name cannot be empty")
        
        name = name.strip()
        
        if len(name) < 1 or len(name) > 255:
            raise ValidationError("Product name must be between 1 and 255 characters")
        
        # Check for potentially dangerous content
        if re.search(r'<script|javascript:|<iframe|<object|<embed', name, re.IGNORECASE):
            raise ValidationError("Product name contains potentially dangerous content")
    
    @staticmethod
    def validate_sku(sku: str) -> None:
        """Validate product SKU"""
        if not sku or not sku.strip():
            raise ValidationError("SKU cannot be empty")
        
        sku = sku.strip().upper()
        
        if len(sku) < 1 or len(sku) > 100:
            raise ValidationError("SKU must be between 1 and 100 characters")
        
        # SKU should only contain letters, numbers, hyphens, and underscores
        if not re.match(r'^[A-Z0-9\-_]+$', sku):
            raise ValidationError("SKU can only contain letters, numbers, hyphens, and underscores")
        
        # SKU shouldn't be all special characters
        if re.match(r'^[\-_]+$', sku):
            raise ValidationError("SKU must contain at least one letter or number")
    
    @staticmethod
    def validate_price(price: float) -> None:
        """Validate product price"""
        if not isinstance(price, (int, float, Decimal)):
            raise ValidationError("Price must be a number")
        
        if price <= 0:
            raise ValidationError("Price must be greater than 0")
        
        if price > 999999.99:
            raise ValidationError("Price cannot exceed $999,999.99")
        
        # Check for reasonable decimal places
        if isinstance(price, float):
            decimal_places = len(str(price).split('.')[-1]) if '.' in str(price) else 0
            if decimal_places > 2:
                raise ValidationError("Price cannot have more than 2 decimal places")
    
    @staticmethod
    def validate_cost_price(cost_price: float, selling_price: float = None) -> None:
        """Validate product cost price"""
        ProductValidator.validate_price(cost_price)
        
        if selling_price and cost_price > selling_price:
            raise ValidationError("Cost price cannot be higher than selling price")
    
    @staticmethod
    def validate_stock_quantity(quantity: int) -> None:
        """Validate stock quantity"""
        if not isinstance(quantity, int):
            raise ValidationError("Stock quantity must be an integer")
        
        if quantity < 0:
            raise ValidationError("Stock quantity cannot be negative")
        
        if quantity > 1000000:
            raise ValidationError("Stock quantity cannot exceed 1,000,000")
    
    @staticmethod
    def validate_min_stock_level(min_level: int, current_stock: int = None) -> None:
        """Validate minimum stock level"""
        if not isinstance(min_level, int):
            raise ValidationError("Minimum stock level must be an integer")
        
        if min_level < 0:
            raise ValidationError("Minimum stock level cannot be negative")
        
        if min_level > 10000:
            raise ValidationError("Minimum stock level cannot exceed 10,000")
        
        if current_stock is not None and min_level > current_stock:
            # This is a warning, not an error
            pass
    
    @staticmethod
    def validate_category(category: str) -> None:
        """Validate product category"""
        if len(category.strip()) > 100:
            raise ValidationError("Category name cannot exceed 100 characters")
        
        # Category should only contain letters, numbers, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-&.,()]+$', category.strip()):
            raise ValidationError("Category contains invalid characters")
    
    @staticmethod
    def validate_brand(brand: str) -> None:
        """Validate product brand"""
        if len(brand.strip()) > 100:
            raise ValidationError("Brand name cannot exceed 100 characters")
        
        # Brand should only contain letters, numbers, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-&.,()]+$', brand.strip()):
            raise ValidationError("Brand contains invalid characters")
    
    @staticmethod
    def validate_description(description: str) -> None:
        """Validate product description"""
        if description and len(description) > 5000:
            raise ValidationError("Description cannot exceed 5000 characters")
        
        # Check for potentially dangerous content
        if description and re.search(r'<script|javascript:|<iframe|<object|<embed', description, re.IGNORECASE):
            raise ValidationError("Description contains potentially dangerous content")
    
    @staticmethod
    def validate_weight(weight: float) -> None:
        """Validate product weight"""
        if not isinstance(weight, (int, float, Decimal)):
            raise ValidationError("Weight must be a number")
        
        if weight <= 0:
            raise ValidationError("Weight must be greater than 0")
        
        if weight > 10000:  # 10 tons
            raise ValidationError("Weight cannot exceed 10,000 kg")
    
    @staticmethod
    def validate_dimensions(dimensions: str) -> None:
        """Validate product dimensions"""
        if len(dimensions.strip()) > 100:
            raise ValidationError("Dimensions cannot exceed 100 characters")
        
        # Basic format validation for dimensions (e.g., "10x20x30 cm")
        if not re.match(r'^[\d\s\.\-xX×cm]+$', dimensions.strip()):
            raise ValidationError("Invalid dimensions format")
    
    @staticmethod
    def validate_color(color: str) -> None:
        """Validate product color"""
        if len(color.strip()) > 50:
            raise ValidationError("Color name cannot exceed 50 characters")
        
        # Color should only contain letters, numbers, and spaces
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', color.strip()):
            raise ValidationError("Color contains invalid characters")
    
    @staticmethod
    def validate_size(size: str) -> None:
        """Validate product size"""
        if len(size.strip()) > 50:
            raise ValidationError("Size cannot exceed 50 characters")
        
        # Size can contain letters, numbers, and basic symbols
        if not re.match(r'^[a-zA-Z0-9\s\-/]+$', size.strip()):
            raise ValidationError("Size contains invalid characters")
    
    @staticmethod
    def validate_material(material: str) -> None:
        """Validate product material"""
        if len(material.strip()) > 100:
            raise ValidationError("Material name cannot exceed 100 characters")
        
        # Material should only contain letters, numbers, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-,&.()]+$', material.strip()):
            raise ValidationError("Material contains invalid characters")
    
    @staticmethod
    def validate_tax_rate(tax_rate: float) -> None:
        """Validate tax rate"""
        if not isinstance(tax_rate, (int, float, Decimal)):
            raise ValidationError("Tax rate must be a number")
        
        if tax_rate < 0 or tax_rate > 1:
            raise ValidationError("Tax rate must be between 0.0 and 1.0 (0% and 100%)")
    
    @staticmethod
    def validate_barcode(barcode: str) -> None:
        """Validate product barcode"""
        if len(barcode.strip()) > 100:
            raise ValidationError("Barcode cannot exceed 100 characters")
        
        # Barcode should only contain numbers and basic separators
        if not re.match(r'^[0-9\-\s]+$', barcode.strip()):
            raise ValidationError("Barcode can only contain numbers, hyphens, and spaces")
        
        # Remove separators and check length
        clean_barcode = re.sub(r'[\-\s]', '', barcode.strip())
        if len(clean_barcode) < 8:
            raise ValidationError("Barcode must be at least 8 digits long")
    
    @staticmethod
    def validate_image_url(url: str) -> None:
        """Validate product image URL"""
        ProductValidator.validate_url(url)
        
        # Check if it's an image URL (basic check)
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if not any(url.lower().endswith(ext) for ext in image_extensions):
            # If no extension, check for common image hosting patterns
            image_hosts = ['imgur.com', 'cloudinary.com', 'amazonaws.com', 'images.', 'img.']
            if not any(host in url.lower() for host in image_hosts):
                raise ValidationError("URL does not appear to be a valid image URL")
    
    @staticmethod
    def validate_product_update_data(update_data: Dict[str, Any]) -> None:
        """Validate product update data"""
        allowed_fields = [
            'name', 'description', 'sku', 'price', 'cost_price', 'stock_quantity',
            'min_stock_level', 'category', 'brand', 'weight', 'dimensions', 'color',
            'size', 'material', 'is_available', 'is_featured', 'is_digital',
            'requires_shipping', 'tax_rate', 'barcode', 'image_url'
        ]
        
        # Check for invalid fields
        invalid_fields = [field for field in update_data.keys() if field not in allowed_fields]
        if invalid_fields:
            raise ValidationError(f"Invalid update fields: {', '.join(invalid_fields)}")
        
        # Validate each field
        for field, value in update_data.items():
            if value is None:
                continue
                
            if field == 'name':
                ProductValidator.validate_product_name(value)
            elif field == 'description':
                ProductValidator.validate_description(value)
            elif field == 'sku':
                ProductValidator.validate_sku(value)
            elif field == 'price':
                ProductValidator.validate_price(value)
            elif field == 'cost_price':
                ProductValidator.validate_cost_price(value, update_data.get('price'))
            elif field == 'stock_quantity':
                ProductValidator.validate_stock_quantity(value)
            elif field == 'min_stock_level':
                ProductValidator.validate_min_stock_level(value, update_data.get('stock_quantity'))
            elif field == 'category':
                ProductValidator.validate_category(value)
            elif field == 'brand':
                ProductValidator.validate_brand(value)
            elif field == 'weight':
                ProductValidator.validate_weight(value)
            elif field == 'dimensions':
                ProductValidator.validate_dimensions(value)
            elif field == 'color':
                ProductValidator.validate_color(value)
            elif field == 'size':
                ProductValidator.validate_size(value)
            elif field == 'material':
                ProductValidator.validate_material(value)
            elif field == 'tax_rate':
                ProductValidator.validate_tax_rate(value)
            elif field == 'barcode':
                ProductValidator.validate_barcode(value)
            elif field == 'image_url':
                ProductValidator.validate_image_url(value)
            elif field in ['is_available', 'is_featured', 'is_digital', 'requires_shipping']:
                if not isinstance(value, bool):
                    raise ValidationError(f"{field} must be a boolean")
    
    @staticmethod
    def validate_bulk_product_data(products_data: List[Dict[str, Any]]) -> None:
        """Validate bulk product creation data"""
        if not products_data:
            raise ValidationError("No product data provided")
        
        if len(products_data) > 1000:
            raise ValidationError("Cannot create more than 1000 products at once")
        
        skus = []
        for i, product_data in enumerate(products_data):
            try:
                # Validate required fields
                required_fields = ['name', 'sku', 'price']
                for field in required_fields:
                    if field not in product_data:
                        raise ValidationError(f"Missing required field: {field}")
                
                # Validate individual product data
                ProductValidator.validate_product_creation_data(
                    name=product_data['name'],
                    sku=product_data['sku'],
                    price=product_data['price'],
                    stock_quantity=product_data.get('stock_quantity', 0),
                    category=product_data.get('category'),
                    brand=product_data.get('brand')
                )
                
                # Check for duplicate SKUs in the batch
                if product_data['sku'] in skus:
                    raise ValidationError(f"Duplicate SKU in batch: {product_data['sku']}")
                skus.append(product_data['sku'])
                
            except ValidationError as e:
                raise ValidationError(f"Product {i+1}: {str(e)}")
    
    @staticmethod
    def validate_product_search_params(
        search_term: str = None,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        skip: int = 0,
        limit: int = 100
    ) -> None:
        """Validate product search parameters"""
        # Validate search term
        if search_term:
            if len(search_term.strip()) < 2:
                raise ValidationError("Search term must be at least 2 characters long")
            
            if len(search_term.strip()) > 100:
                raise ValidationError("Search term cannot exceed 100 characters")
            
            # Check for dangerous patterns
            dangerous_patterns = [r'<script', r'javascript:', r'<iframe', r'<object', r'<embed']
            for pattern in dangerous_patterns:
                if re.search(pattern, search_term, re.IGNORECASE):
                    raise ValidationError("Search term contains potentially dangerous content")
        
        # Validate category
        if category:
            ProductValidator.validate_category(category)
        
        # Validate price range
        if min_price is not None:
            ProductValidator.validate_price(min_price)
        
        if max_price is not None:
            ProductValidator.validate_price(max_price)
        
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationError("Minimum price cannot be greater than maximum price")
        
        # Validate pagination parameters
        ProductValidator.validate_positive_number(skip + 1, "Skip")  # skip can be 0
        ProductValidator.validate_positive_number(limit, "Limit")
        
        if limit > 1000:
            raise ValidationError("Limit cannot exceed 1000")
    
    @staticmethod
    def validate_stock_adjustment(current_stock: int, adjustment: int) -> None:
        """Validate stock adjustment"""
        if not isinstance(adjustment, int):
            raise ValidationError("Stock adjustment must be an integer")
        
        new_stock = current_stock + adjustment
        
        if new_stock < 0:
            raise ValidationError(f"Stock adjustment would result in negative stock ({new_stock})")
        
        if new_stock > 1000000:
            raise ValidationError("Stock adjustment would exceed maximum stock limit")
    
    @staticmethod
    def validate_price_update(current_price: float, new_price: float) -> None:
        """Validate price update"""
        ProductValidator.validate_price(new_price)
        
        # Check for reasonable price changes (optional warning)
        if new_price > current_price * 10:
            # This could be a warning rather than an error
            pass
        
        if new_price < current_price * 0.1:
            # This could be a warning rather than an error
            pass


class ProductInventoryValidator(ProductValidator):
    """Product inventory-specific validators"""
    
    @staticmethod
    def validate_inventory_adjustment(
        product_id: int,
        adjustment_type: str,
        quantity: int,
        reason: str = None
    ) -> None:
        """Validate inventory adjustment"""
        if not isinstance(product_id, int) or product_id <= 0:
            raise ValidationError("Invalid product ID")
        
        valid_adjustment_types = ['increase', 'decrease', 'set', 'restock', 'return', 'damaged', 'lost']
        if adjustment_type not in valid_adjustment_types:
            raise ValidationError(f"Invalid adjustment type. Must be one of: {', '.join(valid_adjustment_types)}")
        
        if not isinstance(quantity, int):
            raise ValidationError("Quantity must be an integer")
        
        if adjustment_type in ['increase', 'restock', 'return'] and quantity <= 0:
            raise ValidationError("Quantity must be positive for increase operations")
        
        if adjustment_type in ['decrease', 'damaged', 'lost'] and quantity <= 0:
            raise ValidationError("Quantity must be positive for decrease operations")
        
        if adjustment_type == 'set' and quantity < 0:
            raise ValidationError("Quantity cannot be negative for set operations")
        
        if reason and len(reason) > 255:
            raise ValidationError("Reason cannot exceed 255 characters")


class ProductPricingValidator(ProductValidator):
    """Product pricing-specific validators"""
    
    @staticmethod
    def validate_pricing_strategy(
        cost_price: float,
        selling_price: float,
        min_margin: float = 0.1
    ) -> None:
        """Validate pricing strategy"""
        ProductValidator.validate_price(cost_price)
        ProductValidator.validate_price(selling_price)
        
        if cost_price >= selling_price:
            raise ValidationError("Selling price must be higher than cost price")
        
        margin = (selling_price - cost_price) / selling_price
        if margin < min_margin:
            raise ValidationError(f"Profit margin ({margin:.1%}) is below minimum required ({min_margin:.1%})")
    
    @staticmethod
    def validate_bulk_price_update(price_updates: List[Dict[str, Any]]) -> None:
        """Validate bulk price update"""
        if not price_updates:
            raise ValidationError("No price updates provided")
        
        if len(price_updates) > 1000:
            raise ValidationError("Cannot update more than 1000 product prices at once")
        
        for i, update in enumerate(price_updates):
            try:
                if 'id' not in update:
                    raise ValidationError("Product ID is required")
                
                if 'price' not in update:
                    raise ValidationError("New price is required")
                
                if not isinstance(update['id'], int) or update['id'] <= 0:
                    raise ValidationError("Invalid product ID")
                
                ProductValidator.validate_price(update['price'])
                
            except ValidationError as e:
                raise ValidationError(f"Price update {i+1}: {str(e)}")
