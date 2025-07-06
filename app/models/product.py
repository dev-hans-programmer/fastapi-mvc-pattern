"""
Product database model.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean
from sqlalchemy.orm import relationship
from decimal import Decimal

from app.models.base import BaseModel


class Product(BaseModel):
    """Product model."""
    
    __tablename__ = "products"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    inventory_count = Column(Integer, default=0, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name})>"
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.inventory_count > 0
    
    @property
    def price_decimal(self) -> Decimal:
        """Get price as decimal."""
        return Decimal(str(self.price))
