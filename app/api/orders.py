
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_customer
from app.database import get_db
from app.models import (
    CartItem,
    Customer,
    Order,
    OrderDelivery,
    OrderItem,
    Product,
)
from app.schemas.order import CheckoutRequest, OrderResponse


router = APIRouter(
    prefix="/api/orders",
    tags=["Customer Orders"],
)


# ==========================================
# ORDER RELATIONSHIPS
# ==========================================

def order_load_options():
    """
    Load order items, their related products,
    and the delivery record.

    Product information is required to return
    product_name and product_image_url.
    """
    return (
        selectinload(Order.items).selectinload(
            OrderItem.product
        ),
        selectinload(Order.delivery),
        selectinload(Order.support_tickets),
    )


# ==========================================
# 1. CHECKOUT
# ==========================================

@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    # --------------------------------------
    # Get authenticated customer's cart
    # --------------------------------------

    cart_items = db.scalars(
        select(CartItem)
        .where(
            CartItem.customer_id == customer.id
        )
        .order_by(
            CartItem.product_id
        )
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty",
        )

    total_amount = Decimal("0.00")

    try:
        # --------------------------------------
        # Create Order
        # --------------------------------------

        order = Order(
            order_number=(
                f"SOL-{uuid4().hex[:12].upper()}"
            ),
            customer_id=customer.id,
            status="pending",
            total_amount=Decimal("0.00"),
        )

        db.add(order)
        db.flush()

        # --------------------------------------
        # Create Delivery Information
        # --------------------------------------

        delivery = OrderDelivery(
            order_id=order.id,
            recipient_name=payload.recipient_name,
            contact_number=payload.contact_number,
            address_line_1=payload.address_line_1,
            address_line_2=payload.address_line_2,
            barangay=payload.barangay,
            city=payload.city,
            province=payload.province,
            postal_code=payload.postal_code,
            country=payload.country,
            delivery_notes=payload.delivery_notes,
            status="pending",
        )

        db.add(delivery)

        # --------------------------------------
        # Process Cart Items
        # --------------------------------------

        for cart_item in cart_items:
            product = db.get(
                Product,
                cart_item.product_id
            )

            if (
                product is None
                or not product.is_active
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A product in your cart "
                        "is unavailable"
                    ),
                )

            if cart_item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid cart item quantity"
                    ),
                )

            # ----------------------------------
            # Update Product Stock
            # ----------------------------------

            result = db.execute(
                update(Product)
                .where(
                    Product.id == product.id,
                    Product.is_active.is_(True),
                    Product.stock_quantity
                    >= cart_item.quantity,
                )
                .values(
                    stock_quantity=(
                        Product.stock_quantity
                        - cart_item.quantity
                    )
                )
                .execution_options(
                    synchronize_session=False
                )
            )

            if result.rowcount != 1:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient stock for "
                        f"{product.name}"
                    ),
                )

            # ----------------------------------
            # Create Order Item
            # ----------------------------------

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=cart_item.quantity,
                unit_price=product.price,
            )

            db.add(order_item)

            total_amount += (
                product.price
                * cart_item.quantity
            )

        # --------------------------------------
        # Update Order Total
        # --------------------------------------

        order.total_amount = total_amount

        # --------------------------------------
        # Clear Customer Cart
        # --------------------------------------

        for cart_item in cart_items:
            db.delete(cart_item)

        # --------------------------------------
        # Commit Transaction
        # --------------------------------------

        db.commit()

    except Exception:
        db.rollback()
        raise

    # ------------------------------------------
    # Fetch Complete Order
    # ------------------------------------------

    saved_order = db.scalar(
        select(Order)
        .options(
            *order_load_options()
        )
        .where(
            Order.id == order.id,
            Order.customer_id == customer.id,
        )
    )

    return saved_order


# ==========================================
# 2. LIST CUSTOMER ORDERS
# ==========================================

@router.get(
    "",
    response_model=List[OrderResponse],
)
def list_orders(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    orders = db.scalars(
        select(Order)
        .options(
            *order_load_options()
        )
        .where(
            Order.customer_id == customer.id
        )
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
    ).all()

    return orders


# ==========================================
# 3. GET ORDER DETAILS
# ==========================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    order = db.scalar(
        select(Order)
        .options(
            *order_load_options()
        )
        .where(
            Order.id == order_id,
            Order.customer_id == customer.id,
        )
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


# ==========================================
# 4. CONFIRM ORDER RECEIVED
# ==========================================

@router.patch(
    "/{order_id}/receive",
    status_code=status.HTTP_200_OK,
)
def confirm_order_received(
    order_id: int,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    """
    Allow the authenticated customer to confirm
    receipt of a delivered order.

    Only orders belonging to the authenticated
    customer can be confirmed.

    Delivery must be in 'delivered' status
    before it can become 'received'.
    """

    # --------------------------------------
    # Find authenticated customer's order
    # --------------------------------------

    order = db.scalar(
        select(Order)
        .options(
            selectinload(Order.delivery)
        )
        .where(
            Order.id == order_id,
            Order.customer_id == customer.id,
        )
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found.",
        )

    # --------------------------------------
    # Validate delivery information
    # --------------------------------------

    delivery = order.delivery

    if delivery is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Delivery information "
                "is unavailable."
            ),
        )

    # --------------------------------------
    # Prevent duplicate confirmation
    # --------------------------------------

    if delivery.status == "received":
        raise HTTPException(
            status_code=400,
            detail=(
                "Order has already been "
                "confirmed as received."
            ),
        )

    # --------------------------------------
    # Require delivered status
    # --------------------------------------

    if delivery.status != "delivered":
        raise HTTPException(
            status_code=400,
            detail=(
                "Only delivered orders can "
                "be confirmed as received."
            ),
        )

    # --------------------------------------
    # Update delivery status atomically
    # --------------------------------------

    received_at = datetime.now(
        timezone.utc
    ).replace(tzinfo=None)

    result = db.execute(
        update(OrderDelivery)
        .where(
            OrderDelivery.id == delivery.id,
            OrderDelivery.status == "delivered",
        )
        .values(
            status="received",
            received_at=received_at,
        )
        .execution_options(
            synchronize_session=False
        )
    )

    if result.rowcount != 1:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Delivery status has changed. "
                "Please refresh your order."
            ),
        )

    # --------------------------------------
    # Update order status
    # --------------------------------------

    order.status = "received"

    # --------------------------------------
    # Save changes
    # --------------------------------------

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # --------------------------------------
    # Return confirmation
    # --------------------------------------

    return {
        "message": (
            "Order confirmed as "
            "received successfully."
        ),
        "order_id": order.id,
        "order_number": order.order_number,
        "order_status": "received",
        "delivery_status": "received",
        "received_at": received_at,
    }
