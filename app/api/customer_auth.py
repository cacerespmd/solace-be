
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.dependencies import get_current_customer
from app.schemas.auth import (
    CustomerRegisterRequest,
    CustomerLoginRequest,
    CustomerResponse,
    CustomerTokenResponse,
)


router = APIRouter(
    prefix="/api/customers/auth",
    tags=["Customer Authentication"],
)


# ==========================================
# REGISTER CUSTOMER
# ==========================================

@router.post(
    "/register",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_customer(
    payload: CustomerRegisterRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    existing_customer = db.scalar(
        select(Customer).where(Customer.email == email)
    )

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        )

    customer = Customer(
        name=payload.name,
        email=email,
        password_hash=hash_password(payload.password),
    )

    db.add(customer)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        )

    db.refresh(customer)

    return customer


# ==========================================
# LOGIN CUSTOMER
# ==========================================

@router.post(
    "/login",
    response_model=CustomerTokenResponse,
)
def login_customer(
    payload: CustomerLoginRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()

    customer = db.scalar(
        select(Customer).where(Customer.email == email)
    )

    if not customer or not verify_password(
        payload.password,
        customer.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        customer.id,
        role="customer",
    )

    return CustomerTokenResponse(
        access_token=access_token,
        customer=customer,
    )


# ==========================================
# GET AUTHENTICATED CUSTOMER
# ==========================================

@router.get(
    "/me",
    response_model=CustomerResponse,
)
def get_customer_profile(
    current_customer: Customer = Depends(get_current_customer),
):
    return current_customer
