
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    Order,
    OrderDelivery,
    OrderItem,
    Customer,
)

from app.core.dependencies import get_current_admin


router = APIRouter(
    prefix="/api/admin/orders",
    tags=["Admin Orders"],
    dependencies=[Depends(get_current_admin)],
)


REFUND_RETURN_CATEGORIES = {
    "refund_request",
    "return_request",
    "damaged_item",
    "wrong_item",
    "missing_item",
}

REFUND_RETURN_STATUS_LABELS = {
    "open": "Refund/Return Requested",
    "in_process": "Refund/Return In Process",
    "return_accepted": "Return Accepted",
    "return_declined": "Return Declined",
    "refund_accepted": "Refund Accepted",
    "refund_declined": "Refund Declined",
    "returned": "Returned",
    "refunded": "Refunded",
}


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ShipOrderRequest(BaseModel):
    courier_name: Optional[str] = Field(
        default=None,
        max_length=150,
    )
    tracking_number: Optional[str] = Field(
        default=None,
        max_length=150,
    )


class DeliveryStatusRequest(BaseModel):
    status: Literal[
        "shipped",
        "out_for_delivery",
        "delivered",
        "failed",
    ]


def serialize_support_ticket(ticket):
    return {
        "id": ticket.id,
        "customer_id": ticket.customer_id,
        "order_id": ticket.order_id,
        "category": ticket.category,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": (
            ticket.created_at.isoformat()
            if ticket.created_at
            else None
        ),
        "updated_at": (
            ticket.updated_at.isoformat()
            if ticket.updated_at
            else None
        ),
    }


def get_latest_refund_return_ticket(order):
    tickets = [
        ticket
        for ticket in order.support_tickets
        if ticket.category
        and ticket.category.lower() in REFUND_RETURN_CATEGORIES
    ]

    if not tickets:
        return None

    return max(
        tickets,
        key=lambda ticket: (
            ticket.created_at or datetime.min,
            ticket.id,
        ),
    )


def get_display_status(order):
    ticket = get_latest_refund_return_ticket(order)

    if ticket is not None:
        return {
            "status": ticket.status,
            "label": REFUND_RETURN_STATUS_LABELS.get(
                ticket.status,
                ticket.status.replace("_", " ").title(),
            ),
            "source": "support_ticket",
            "ticket_id": ticket.id,
        }

    status = order.status or "pending"

    return {
        "status": status,
        "label": status.replace("_", " ").title(),
        "source": "order",
        "ticket_id": None,
    }


def serialize_order(order):
    delivery = order.delivery

    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer": {
            "id": order.customer.id,
            "name": order.customer.name,
            "email": order.customer.email,
        },
        "status": order.status,
        "display_status": get_display_status(order),
        "total_amount": float(order.total_amount),
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "image_url": item.product.image_url,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price),
            }
            for item in order.items
        ],
        "support_tickets": [
            serialize_support_ticket(ticket)
            for ticket in sorted(
                order.support_tickets,
                key=lambda ticket: (
                    ticket.created_at or datetime.min,
                    ticket.id,
                ),
                reverse=True,
            )
        ],
        "delivery": (
            {
                "id": delivery.id,
                "status": delivery.status,
                "recipient_name": delivery.recipient_name,
                "contact_number": delivery.contact_number,
                "address_line_1": delivery.address_line_1,
                "address_line_2": delivery.address_line_2,
                "barangay": delivery.barangay,
                "city": delivery.city,
                "province": delivery.province,
                "postal_code": delivery.postal_code,
                "country": delivery.country,
                "delivery_notes": delivery.delivery_notes,
                "courier_name": delivery.courier_name,
                "tracking_number": delivery.tracking_number,
                "shipped_at": (
                    delivery.shipped_at.isoformat()
                    if delivery.shipped_at
                    else None
                ),
                "delivered_at": (
                    delivery.delivered_at.isoformat()
                    if delivery.delivered_at
                    else None
                ),
                "received_at": (
                    delivery.received_at.isoformat()
                    if delivery.received_at
                    else None
                ),
            }
            if delivery
            else None
        ),
    }


def get_order_or_404(db, order_id):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.delivery),
            joinedload(Order.items).joinedload(
                OrderItem.product
            ),
            joinedload(Order.support_tickets),
        )
        .filter(Order.id == order_id)
        .first()
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found.",
        )

    return order


@router.get("")
def list_orders(
    search: Optional[str] = None,
    delivery_status: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Order)

    if search:
        query = query.join(Customer).filter(
            or_(
                Order.order_number.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%"),
            )
        )

    if delivery_status:
        query = query.join(OrderDelivery).filter(
            OrderDelivery.status == delivery_status
        )

    total = query.count()

    orders = (
        query.options(
            joinedload(Order.customer),
            joinedload(Order.delivery),
            joinedload(Order.items).joinedload(
                OrderItem.product
            ),
            joinedload(Order.support_tickets),
        )
        .order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "orders": [
            serialize_order(order)
            for order in orders
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)
    return serialize_order(order)


@router.patch("/{order_id}/ship")
def ship_order(
    order_id: int,
    payload: ShipOrderRequest,
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)

    if order.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cancelled orders cannot be shipped.")

    delivery = order.delivery

    if delivery is None:
        raise HTTPException(
            status_code=400,
            detail="This order has no delivery record.",
        )

    if delivery.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending deliveries can be shipped.",
        )

    delivery.status = "shipped"
    delivery.shipped_at = utc_now()
    delivery.courier_name = payload.courier_name
    delivery.tracking_number = payload.tracking_number

    order.status = "shipped"

    db.commit()
    db.refresh(order)

    return {
        "message": "Order shipped successfully.",
        "order": serialize_order(
            get_order_or_404(db, order_id)
        ),
    }


@router.patch("/{order_id}/delivery-status")
def update_delivery_status(
    order_id: int,
    payload: DeliveryStatusRequest,
    db: Session = Depends(get_db),
):
    order = get_order_or_404(db, order_id)

    delivery = order.delivery

    if delivery is None:
        raise HTTPException(
            status_code=400,
            detail="This order has no delivery record.",
        )

    allowed_transitions = {
        "shipped": {
            "out_for_delivery",
            "failed",
        },
        "out_for_delivery": {
            "delivered",
            "failed",
        },
        "delivered": set(),
        "received": set(),
        "failed": set(),
        "pending": set(),
    }

    allowed = allowed_transitions.get(
        delivery.status,
        set(),
    )

    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change delivery status from "
                f"{delivery.status} to {payload.status}."
            ),
        )

    delivery.status = payload.status

    if payload.status == "delivered":
        delivery.delivered_at = utc_now()

    order.status = payload.status

    db.commit()
    db.refresh(order)

    return {
        "message": "Delivery status updated successfully.",
        "order": serialize_order(
            get_order_or_404(db, order_id)
        ),
    }
