from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin
from app.database import get_db
from app.models import Customer, Order
from app.schemas.auth import CustomerResponse


router = APIRouter(
    prefix="/api/admin/customers",
    tags=["Admin Customers"],
    dependencies=[Depends(get_current_admin)],
)


class AdminCustomerResponse(CustomerResponse):
    orders_count: int


class CustomerDirectoryResponse(BaseModel):
    customers: list[AdminCustomerResponse]
    total: int
    page: int
    per_page: int


def customer_with_order_count(
    customer: Customer,
    orders_count: int,
) -> AdminCustomerResponse:
    return AdminCustomerResponse(
        **CustomerResponse.model_validate(customer).model_dump(),
        orders_count=orders_count,
    )


@router.get("", response_model=CustomerDirectoryResponse)
def list_customers(
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Customer)

    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
            )
        )

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    orders_count = (
        select(func.count(Order.id))
        .where(Order.customer_id == Customer.id)
        .correlate(Customer)
        .scalar_subquery()
    )
    customers = db.execute(
        query.add_columns(orders_count.label("orders_count"))
        .order_by(
            Customer.created_at.desc(),
            Customer.id.desc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    return {
        "customers": [
            customer_with_order_count(customer, count)
            for customer, count in customers
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{customer_id}", response_model=AdminCustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    customer_with_count = db.execute(
        select(
            Customer,
            select(func.count(Order.id))
            .where(Order.customer_id == Customer.id)
            .correlate(Customer)
            .scalar_subquery()
            .label("orders_count"),
        ).where(Customer.id == customer_id)
    ).one_or_none()

    if customer_with_count is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found.",
        )

    customer, orders_count = customer_with_count
    return customer_with_order_count(customer, orders_count)
