"""
Order database models.
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from app.models.base import BaseModel


class Order(BaseModel):
    """Order model."""
    
    __tablename__ = "orders"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def total_amount_decimal(self) -> Decimal:
        """Get total amount as decimal."""
        return Decimal(str(self.total_amount))
    
    @property
    def item_count(self) -> int:
        """Get number of items in order."""
        return len(self.items)


class OrderItem(BaseModel):
    """Order item model."""
    
    __tablename__ = "order_items"
    
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"
    
    @property
    def unit_price_decimal(self) -> Decimal:
        """Get unit price as decimal."""
        return Decimal(str(self.unit_price))
    
    @property
    def total_price_decimal(self) -> Decimal:
        """Get total price as decimal."""
        return Decimal(str(self.total_price))
