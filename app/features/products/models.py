"""
Product models
"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class ProductStatus(enum.Enum):
    """Product status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"


class ProductType(enum.Enum):
    """Product type enumeration."""
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"


class Product(Base):
    """Product model."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(200), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))
    slug = Column(String(250), unique=True, nullable=False, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    compare_price = Column(Numeric(10, 2))  # Original price for discounts
    
    # Inventory
    track_inventory = Column(Boolean, default=True)
    inventory_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)
    allow_backorder = Column(Boolean, default=False)
    
    # Product details
    weight = Column(Numeric(8, 3))  # in kg
    dimensions_length = Column(Numeric(8, 2))  # in cm
    dimensions_width = Column(Numeric(8, 2))
    dimensions_height = Column(Numeric(8, 2))
    
    # Status and type
    status = Column(String(20), default=ProductStatus.ACTIVE.value)
    product_type = Column(String(20), default=ProductType.PHYSICAL.value)
    
    # SEO and metadata
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    tags = Column(ARRAY(String))
    
    # Media
    image_url = Column(String(500))
    image_urls = Column(ARRAY(String))  # Multiple images
    
    # Organization
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    brand_id = Column(UUID(as_uuid=True), ForeignKey("product_brands.id"))
    
    # Flags
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)
    requires_shipping = Column(Boolean, default=True)
    is_taxable = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    brand = relationship("ProductBrand", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")
    reviews = relationship("ProductReview", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    
    @hybrid_property
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        return self.inventory_quantity > 0 or self.allow_backorder
    
    @hybrid_property
    def is_low_stock(self):
        """Check if product is low in stock."""
        if not self.track_inventory:
            return False
        return self.inventory_quantity <= self.low_stock_threshold
    
    @hybrid_property
    def discount_percentage(self):
        """Calculate discount percentage."""
        if self.compare_price and self.compare_price > self.price:
            return ((self.compare_price - self.price) / self.compare_price) * 100
        return 0
    
    def __repr__(self):
        return f"<Product {self.name}>"


class ProductCategory(Base):
    """Product category model."""
    
    __tablename__ = "product_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    image_url = Column(String(500))
    
    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"))
    sort_order = Column(Integer, default=0)
    
    # SEO
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship("ProductCategory", remote_side=[id])
    children = relationship("ProductCategory")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<ProductCategory {self.name}>"


class ProductBrand(Base):
    """Product brand model."""
    
    __tablename__ = "product_brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    logo_url = Column(String(500))
    website_url = Column(String(500))
    
    # SEO
    meta_title = Column(String(200))
    meta_description = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="brand")
    
    def __repr__(self):
        return f"<ProductBrand {self.name}>"


class ProductVariant(Base):
    """Product variant model for products with variations."""
    
    __tablename__ = "product_variants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Variant details
    name = Column(String(200), nullable=False)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    
    # Pricing (can override product pricing)
    price = Column(Numeric(10, 2))
    cost_price = Column(Numeric(10, 2))
    compare_price = Column(Numeric(10, 2))
    
    # Inventory
    inventory_quantity = Column(Integer, default=0)
    
    # Physical attributes
    weight = Column(Numeric(8, 3))
    dimensions_length = Column(Numeric(8, 2))
    dimensions_width = Column(Numeric(8, 2))
    dimensions_height = Column(Numeric(8, 2))
    
    # Media
    image_url = Column(String(500))
    
    # Variant options (e.g., color, size)
    option1 = Column(String(100))  # e.g., "Red"
    option2 = Column(String(100))  # e.g., "Large"
    option3 = Column(String(100))  # e.g., "Cotton"
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    order_items = relationship("OrderItem", back_populates="variant")
    
    @hybrid_property
    def display_name(self):
        """Get variant display name."""
        options = [opt for opt in [self.option1, self.option2, self.option3] if opt]
        if options:
            return f"{self.product.name} - {' / '.join(options)}"
        return self.name
    
    def __repr__(self):
        return f"<ProductVariant {self.display_name}>"


class ProductReview(Base):
    """Product review model."""
    
    __tablename__ = "product_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Review content
    title = Column(String(200))
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    
    # Verification
    is_verified_purchase = Column(Boolean, default=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"))
    
    # Moderation
    is_approved = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Helpful votes
    helpful_count = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User")
    order = relationship("Order")
    
    @hybrid_property
    def helpful_percentage(self):
        """Calculate helpful percentage."""
        if self.total_votes == 0:
            return 0
        return (self.helpful_count / self.total_votes) * 100
    
    def __repr__(self):
        return f"<ProductReview {self.product.name} - {self.rating} stars>"


class ProductAttribute(Base):
    """Product attributes for additional product specifications."""
    
    __tablename__ = "product_attributes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Attribute details
    name = Column(String(100), nullable=False)
    value = Column(String(500), nullable=False)
    type = Column(String(50), default="text")  # text, number, boolean, date
    
    # Display
    display_order = Column(Integer, default=0)
    is_searchable = Column(Boolean, default=False)
    is_comparable = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product")
    
    def __repr__(self):
        return f"<ProductAttribute {self.name}: {self.value}>"
