from typing import Optional

from sqlalchemy.orm import Session

from app.models import Order


def lookup_customer_orders(
    db: Session,
    customer_id: int,
    order_id: Optional[int] = None,
    order_number: Optional[str] = None,
):
    """
    Retrieve orders belonging to the authenticated customer.

    customer_id must come from the authenticated JWT,
    never from AI-generated tool arguments.
    """

    query = db.query(Order).filter(
        Order.customer_id == customer_id
    )

    if order_id is not None:
        query = query.filter(Order.id == order_id)
    elif order_number is not None:
        query = query.filter(
            Order.order_number == order_number.strip().upper()
        )
    else:
        query = query.order_by(
            Order.created_at.desc(),
            Order.id.desc(),
        ).limit(5)

    orders = query.all()

    if not orders:
        return {
            "found": False,
            "message": "No matching orders found for this customer.",
            "orders": [],
        }

    return {
        "found": True,
        "orders": [
            {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat(),
            }
            for order in orders
        ],
    }