
from sqlalchemy.orm import Session

from app.models import Order, SupportTicket


def lookup_support_tickets(
    db: Session,
    customer_id: int,
    order_number: str,
):
    order_number = order_number.strip().upper()

    order = (
        db.query(Order)
        .filter(
            Order.customer_id == customer_id,
            Order.order_number == order_number,
        )
        .first()
    )

    if not order:
        return {
            "found": False,
            "message": (
                "No matching order was found in your account. "
                "Please check your order number."
            ),
            "tickets": [],
        }

    tickets = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.customer_id == customer_id,
            SupportTicket.order_id == order.id,
        )
        .order_by(
            SupportTicket.created_at.desc(),
            SupportTicket.id.desc(),
        )
        .all()
    )

    return {
        "found": True,
        "order_number": order.order_number,
        "tickets": [
            {
                "id": ticket.id,
                "category": ticket.category,
                "subject": ticket.subject,
                "description": ticket.description,
                "status": ticket.status,
                "priority": ticket.priority,
                "created_at": (
                    ticket.created_at.isoformat()
                    if ticket.created_at else None
                ),
                "updated_at": (
                    ticket.updated_at.isoformat()
                    if ticket.updated_at else None
                ),
            }
            for ticket in tickets
        ],
    }
