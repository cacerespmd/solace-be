
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_customer
from app.database import get_db
from app.models import CartItem, Customer, Product
from app.schemas.cart import (
    AddCartItemRequest,
    UpdateCartItemRequest,
    CartResponse,
)


router = APIRouter(
    prefix="/api/cart",
    tags=["Shopping Cart"],
)


def build_cart_response(db: Session, customer_id: int):
    items = db.scalars(
        select(CartItem)
        .options(selectinload(CartItem.product))
        .where(CartItem.customer_id == customer_id)
        .order_by(CartItem.id.desc())
    ).all()

    response_items = []
    total_items = 0
    total_amount = Decimal("0.00")

    for item in items:
        subtotal = item.product.price * item.quantity

        response_items.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "product": item.product,
            "subtotal": subtotal,
        })

        total_items += item.quantity
        total_amount += subtotal

    return {
        "items": response_items,
        "total_items": total_items,
        "total_amount": total_amount,
    }


@router.get("", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    return build_cart_response(db, customer.id)


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_cart(
    payload: AddCartItemRequest,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    product = db.get(Product, payload.product_id)

    if product is None or not product.is_active:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    existing_item = db.scalar(
        select(CartItem).where(
            CartItem.customer_id == customer.id,
            CartItem.product_id == product.id,
        )
    )

    current_quantity = existing_item.quantity if existing_item else 0
    new_quantity = current_quantity + payload.quantity

    if new_quantity > product.stock_quantity:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock",
        )

    if existing_item:
        existing_item.quantity = new_quantity
    else:
        db.add(
            CartItem(
                customer_id=customer.id,
                product_id=product.id,
                quantity=payload.quantity,
            )
        )

    db.commit()

    return build_cart_response(db, customer.id)


@router.patch("/{item_id}", response_model=CartResponse)
def update_cart_item(
    item_id: int,
    payload: UpdateCartItemRequest,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    item = db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.customer_id == customer.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    product = db.get(Product, item.product_id)

    if product is None or not product.is_active:
        raise HTTPException(
            status_code=400,
            detail="Product is no longer available",
        )

    if payload.quantity > product.stock_quantity:
        raise HTTPException(
            status_code=400,
            detail="Requested quantity exceeds available stock",
        )

    item.quantity = payload.quantity
    db.commit()

    return build_cart_response(db, customer.id)


@router.delete("/{item_id}", response_model=CartResponse)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    customer: Customer = Depends(get_current_customer),
):
    item = db.scalar(
        select(CartItem).where(
            CartItem.id == item_id,
            CartItem.customer_id == customer.id,
        )
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found",
        )

    db.delete(item)
    db.commit()

    return build_cart_response(db, customer.id)
