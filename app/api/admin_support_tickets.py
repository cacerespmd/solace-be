
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Order, SupportTicket
from app.schemas.support_ticket import SupportTicketResponse

from app.core.dependencies import get_current_admin


router = APIRouter(
    prefix="/api/admin/support-tickets",
    tags=["Admin Support Tickets"],
    dependencies=[Depends(get_current_admin)],
)


# ==========================================
# SUPPORT TICKET STATUSES
# ==========================================

TicketStatus = Literal[
    "cancellation_accepted",
    "cancellation_declined",
    "open",
    "in_process",
    "return_accepted",
    "return_declined",
    "refund_accepted",
    "refund_declined",
    "returned",
    "refunded",
]


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


# ==========================================
# ALLOWED STATUS TRANSITIONS
# ==========================================

ALLOWED_TRANSITIONS = {
    "open": ["in_process"],

    "in_process": [
        "return_accepted",
        "return_declined",
        "refund_accepted",
        "refund_declined",
    ],

    "return_accepted": ["returned"],

    "refund_accepted": ["refunded"],

    "return_declined": [],
    "refund_declined": [],
    "returned": [],
    "refunded": [],
}


RETURN_CATEGORIES = {
    "return_request",
    "damaged_item",
    "wrong_item",
    "missing_item",
}

REFUND_CATEGORIES = {
    "refund_request",
    "damaged_item",
    "wrong_item",
    "missing_item",
}


# ==========================================
# GET ALL SUPPORT TICKETS
# ==========================================

@router.get(
    "",
    response_model=list[SupportTicketResponse],
)
def get_all_support_tickets(
    db: Session = Depends(get_db),
):
    tickets = db.scalars(
        select(SupportTicket).order_by(
            SupportTicket.created_at.desc()
        )
    ).all()

    return tickets


# ==========================================
# GET SINGLE SUPPORT TICKET
# ==========================================

@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def get_support_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    ticket = db.get(SupportTicket, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found.",
        )

    return ticket


# ==========================================
# UPDATE SUPPORT TICKET STATUS
# ==========================================

@router.patch(
    "/{ticket_id}/status",
    response_model=SupportTicketResponse,
)
def update_support_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
):
    ticket = db.get(SupportTicket, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found.",
        )

    current_status = ticket.status
    new_status = payload.status

    # Decide cancellation and update the order in the same transaction.
    if new_status in {"cancellation_accepted", "cancellation_declined"}:
        if ticket.category not in {"cancellation_request", "cancellation_requested"}:
            raise HTTPException(status_code=400, detail="This is not a cancellation request.")
        order = db.scalar(
            select(Order).where(Order.id == ticket.order_id).with_for_update()
        )
        if order is None or order.customer_id != ticket.customer_id:
            raise HTTPException(status_code=400, detail="No matching order for this request.")
        # Serialize decisions for this order and re-read the ticket after locking.
        db.refresh(ticket)
        if ticket.status == new_status:
            return ticket
        if ticket.status not in {"open", "in_process", "cancellation_requested"}:
            raise HTTPException(status_code=400, detail="This request has already been decided.")
        if new_status == "cancellation_accepted":
            if order.status != "pending" or (
                order.delivery is not None
                and order.delivery.status not in {"pending", "preparing"}
            ):
                raise HTTPException(status_code=400, detail="Only pending, unshipped orders can be cancelled.")
            order.status = "cancelled"
        # Creating a request does not change order.status. Rejection preserves it.
        ticket.status = new_status
        db.commit()
        db.refresh(ticket)
        return ticket

    # No changes needed
    if current_status == new_status:
        return ticket

    # Validate transition
    allowed_statuses = ALLOWED_TRANSITIONS.get(
        current_status, []
    )

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot change status from "
                f"'{current_status}' to '{new_status}'."
            ),
        )

    # Validate return decision
    if new_status.startswith("return_"):
        if ticket.category not in RETURN_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail="This ticket is not eligible for a return.",
            )

    # Validate refund decision
    if new_status.startswith("refund_"):
        if ticket.category not in REFUND_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail="This ticket is not eligible for a refund.",
            )

    # Update ticket
    ticket.status = new_status

    db.commit()
    db.refresh(ticket)

    return ticket
