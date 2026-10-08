from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), default="customer", nullable=False)  # customer, restaurant_staff, admin
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="customer")
    cart = relationship("Cart", back_populates="customer", uselist=False)
    managed_restaurant = relationship("Restaurant", foreign_keys=[restaurant_id])


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    cuisine_type = Column(String(50), nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    food_items = relationship("FoodItem", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(300), nullable=True)
    canonical_price = Column(Float, nullable=False)  # Authoritative source of price
    category = Column(String(50), default="General", nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = relationship("Restaurant", back_populates="food_items")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    cart = relationship("Cart", back_populates="items")
    food_item = relationship("FoodItem")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    subtotal_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=3.00, nullable=False)
    total_amount = Column(Float, nullable=False)  # Calculated server-side
    status = Column(String(30), default="PLACED", nullable=False)  # PLACED, ACCEPTED, REJECTED, PREPARING, OUT_FOR_DELIVERY, DELIVERED, CANCELLED
    delivery_address = Column(String(250), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    snapshot_unit_price = Column(Float, nullable=False)  # Price snapshot at order time
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    food_item = relationship("FoodItem")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    transaction_reference = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_status = Column(String(30), default="SUCCESS", nullable=False)
    payment_token_masked = Column(String(50), nullable=False)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    order = relationship("Order", back_populates="payment")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(String(60), nullable=False)
    entity_name = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    status_result = Column(String(20), default="SUCCESS", nullable=False)
    client_ip = Column(String(50), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
