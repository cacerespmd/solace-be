
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.core.dependencies import get_current_customer
from app.models import Customer, Order, SupportTicket
from app.schemas.support_ticket import (
    SupportTicketCreate,
    SupportTicketResponse,
    SupportTicketListResponse,
)


router = APIRouter(
    prefix="/api/support-tickets",
    tags=["Customer Support Tickets"],
)


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


# ==========================================
# CREATE SUPPORT TICKET
# ==========================================

@router.post(
    "",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    payload: SupportTicketCreate,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    if (
        payload.category in ORDER_REQUIRED_CATEGORIES
        and payload.order_id is None
    ):
        raise HTTPException(
            status_code=422,
            detail="An order is required for this ticket category.",
        )

    if payload.order_id is not None:
        order = db.scalar(
            select(Order)
            .options(selectinload(Order.delivery))
            .where(
                Order.id == payload.order_id,
                Order.customer_id == customer.id,
            )
        )

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found.",
            )

        if order.status.lower() == "pending":
            if payload.category != "cancellation_request":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Only cancellation requests are allowed "
                        "for pending orders."
                    ),
                )

            reason_prefix = "Cancellation request:"
            if (
                not payload.subject.startswith(reason_prefix)
                or len(payload.subject[len(reason_prefix):].strip()) < 5
            ):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Include the cancellation reason in the subject "
                        "as 'Cancellation request: <reason>'."
                    ),
                )
        elif payload.category == "cancellation_request":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Cancellation requests are only available "
                    "for pending orders."
                ),
            )

        if payload.category in RECEIVED_REQUIRED_CATEGORIES:
            if (
                order.delivery is None
                or order.delivery.status != "received"
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "You must confirm receipt of your order "
                        "before requesting a return, refund, "
                        "or reporting an item issue."
                    ),
                )

    ticket = SupportTicket(
        customer_id=customer.id,
        order_id=payload.order_id,
        category=payload.category,
        subject=payload.subject,
        description=payload.description,
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

    return ticket


# ==========================================
# GET MY SUPPORT TICKETS
# ==========================================

@router.get(
    "",
    response_model=SupportTicketListResponse,
)
def get_my_tickets(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    tickets = db.scalars(
        select(SupportTicket)
        .where(SupportTicket.customer_id == customer.id)
        .order_by(
            SupportTicket.created_at.desc(),
            SupportTicket.id.desc(),
        )
    ).all()

    return SupportTicketListResponse(
        tickets=tickets,
    )


# ==========================================
# GET SUPPORT TICKET DETAILS
# ==========================================

@router.get(
    "/{ticket_id}",
    response_model=SupportTicketResponse,
)
def get_ticket_details(
    ticket_id: int,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    ticket = db.scalar(
        select(SupportTicket)
        .where(
            SupportTicket.id == ticket_id,
            SupportTicket.customer_id == customer.id,
        )
    )

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Support ticket not found.",
        )

    return ticket
