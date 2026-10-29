
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Order, SupportTicket


RECEIVED_REQUIRED_CATEGORIES = {
    "return_request",
    "refund_request",
    "damaged_item",
    "wrong_item",
    "missing_item",
}

ORDER_REQUIRED_CATEGORIES = (
    RECEIVED_REQUIRED_CATEGORIES
    | {"delivery_issue", "cancellation_request"}
)

ALLOWED_CATEGORIES = (
    ORDER_REQUIRED_CATEGORIES | {"general"}
)


def create_support_ticket(
    db: Session,
    customer_id: int,
    order_id: int,
    category: str,
    subject: str,
    description: str,
    cancellation_reason: Optional[str] = None,
):
    if category not in ALLOWED_CATEGORIES:
        return {
            "success": False,
            "error": "Invalid support ticket category.",
        }

    if (
        category in ORDER_REQUIRED_CATEGORIES
        and order_id is None
    ):
        return {
            "success": False,
            "error": "An order is required for this request.",
        }

    if not isinstance(subject, str) or not (
        5 <= len(subject.strip()) <= 255
    ):
        return {
            "success": False,
            "error": "Subject must contain 5 to 255 characters.",
        }

    if not isinstance(description, str) or not (
        10 <= len(description.strip()) <= 5000
    ):
        return {
            "success": False,
            "error": "Description must contain 10 to 5000 characters.",
        }

    if order_id is not None:
        if type(order_id) is not int or order_id <= 0:
            return {
                "success": False,
                "error": "Invalid order ID.",
            }

        order = db.scalar(
            select(Order)
            .options(selectinload(Order.delivery))
            .where(
                Order.id == order_id,
                Order.customer_id == customer_id,
            )
        )

        if order is None:
            return {
                "success": False,
                "error": "Order not found.",
            }

        if order.status.lower() == "pending":
            if category != "cancellation_request":
                return {
                    "success": False,
                    "requires_cancellation": True,
                    "error": (
                        "This order is pending. Only a cancellation "
                        "request can be submitted for a pending order. "
                        "Ask the customer whether they want to cancel "
                        "and collect their reason."
                    ),
                }

            if (
                not isinstance(cancellation_reason, str)
                or not 5
                <= len(cancellation_reason.strip())
                <= 255 - len("Cancellation request: ")
            ):
                return {
                    "success": False,
                    "requires_cancellation_reason": True,
                    "error": (
                        "Ask for a cancellation reason that fits in the "
                        "ticket subject before creating the ticket."
                    ),
                }

            subject = (
                "Cancellation request: "
                + cancellation_reason.strip()
            )
            description = "Customer requested cancellation of the order."
        elif category == "cancellation_request":
            return {
                "success": False,
                "error": (
                    "Cancellation requests are only available for "
                    "pending orders."
                ),
            }

        if category in RECEIVED_REQUIRED_CATEGORIES:
            if (
                order.delivery is None
                or order.delivery.status != "received"
            ):
                return {
                    "success": False,
                    "error": (
                        "You must confirm receipt of your "
                        "order before requesting a return, "
                        "refund, or reporting an item issue."
                    ),
                }

        existing_ticket = db.scalar(
            select(SupportTicket)
            .where(
                SupportTicket.customer_id == customer_id,
                SupportTicket.order_id == order_id,
                SupportTicket.category == category,
                SupportTicket.status.in_(("open", "in_process")),
            )
            .order_by(
                SupportTicket.created_at.desc(),
                SupportTicket.id.desc(),
            )
            .limit(1)
        )
        if existing_ticket is not None:
            return {
                "success": True,
                "already_exists": True,
                "created": False,
                "ticket_id": existing_ticket.id,
                "category": existing_ticket.category,
                "status": existing_ticket.status,
                "message": (
                    "An open support ticket already exists for this "
                    "order and category. No duplicate ticket was created."
                ),
            }

    ticket = SupportTicket(
        customer_id=customer_id,
        order_id=order_id,
        category=category,
        subject=subject.strip(),
        description=description.strip(),
        status="open",
        priority="normal",
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "created": True,
        "ticket_id": ticket.id,
        "category": ticket.category,
        "status": ticket.status,
        "message": "Support ticket created successfully.",
    }
