
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ==========================================
# 1. ADMIN
# ==========================================

class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )


# ==========================================
# 2. CUSTOMER
# ==========================================

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer"
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="customer"
    )

    support_tickets: Mapped[list["SupportTicket"]] = relationship(
        back_populates="customer"
    )


# ==========================================
# 3. PRODUCT
# ==========================================

class Product(Base):
    __tablename__ = "products"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="ck_products_price_nonnegative"
        ),
        CheckConstraint(
            "stock_quantity >= 0",
            name="ck_products_stock_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    sku: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    image_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    documents: Mapped[list["ProductDocument"]] = relationship(
        back_populates="product"
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="product"
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product"
    )


# ==========================================
# 4. PRODUCT DOCUMENT
# ==========================================

class ProductDocument(Base):
    __tablename__ = "product_documents"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    document_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    product: Mapped["Product"] = relationship(
        back_populates="documents"
    )


# ==========================================
# 5. CART ITEM
# ==========================================

class CartItem(Base):
    __tablename__ = "cart_items"

    __table_args__ = (
        UniqueConstraint(
            "customer_id",
            "product_id",
            name="uq_cart_customer_product"
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_cart_quantity_positive"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="cart_items"
    )

    product: Mapped["Product"] = relationship(
        back_populates="cart_items"
    )


# ==========================================
# 6. ORDER
# ==========================================

class Order(Base):
    __tablename__ = "orders"

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_orders_total_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="orders"
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order"
    )

    delivery: Mapped[Optional["OrderDelivery"]] = relationship(
        back_populates="order",
        uselist=False
    )

    support_tickets: Mapped[list["SupportTicket"]] = relationship(
        back_populates="order"
    )


# ==========================================
# 7. ORDER ITEM
# ==========================================

class OrderItem(Base):
    __tablename__ = "order_items"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive"
        ),
        CheckConstraint(
            "unit_price >= 0",
            name="ck_order_items_price_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    order: Mapped["Order"] = relationship(
        back_populates="items"
    )

    product: Mapped["Product"] = relationship(
        back_populates="order_items"
    )



# ==========================================
# 8. SUPPORT TICKET
# ==========================================


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="support_tickets"
    )

    order: Mapped[Optional["Order"]] = relationship(
        back_populates="support_tickets"
    )


    # --------------------------------------
    # Ticket details
    # --------------------------------------

    category: Mapped[str] = mapped_column(
        String(50),
        default="general",
        nullable=False
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # --------------------------------------
    # Ticket status
    # --------------------------------------

    status: Mapped[str] = mapped_column(
        String(50),
        default="open",
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False
    )

    # --------------------------------------
    # Timestamps
    # --------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # --------------------------------------
    # Relationships
    # --------------------------------------

    customer: Mapped["Customer"] = relationship(
        back_populates="support_tickets"
    )

    order: Mapped[Optional["Order"]] = relationship(
        back_populates="support_tickets"
    )


class PendingSupportAction(Base):
    __tablename__ = "pending_support_actions"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        primary_key=True,
    )

    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id"),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )



# ==========================================
# 9. ORDER DELIVERY
# ==========================================

class OrderDelivery(Base):
    __tablename__ = "order_deliveries"

    __table_args__ = (
        CheckConstraint(
            "status IN ("
            "'pending', "
            "'shipped', "
            "'out_for_delivery', "
            "'delivered', "
            "'received', "
            "'failed'"
            ")",
            name="ck_order_deliveries_status"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        unique=True,
        nullable=False
    )

    # --------------------------------------
    # Recipient information
    # --------------------------------------

    recipient_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    contact_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # --------------------------------------
    # Delivery address
    # --------------------------------------

    address_line_1: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    address_line_2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    barangay: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    province: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(100),
        default="Philippines",
        nullable=False
    )

    delivery_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # --------------------------------------
    # Courier and tracking
    # --------------------------------------

    courier_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )

    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True
    )

    # --------------------------------------
    # Delivery status
    # --------------------------------------

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False
    )

    shipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # --------------------------------------
    # Timestamps
    # --------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # --------------------------------------
    # Relationships
    # --------------------------------------

    order: Mapped["Order"] = relationship(
        back_populates="delivery"
    )
