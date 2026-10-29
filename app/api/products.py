
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Admin, Product
from app.core.dependencies import get_current_admin
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
)


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


@router.get("", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return db.scalars(
        select(Product)
        .options(selectinload(Product.documents))
        .where(Product.is_active.is_(True))
        .order_by(Product.id.desc())
    ).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    product = db.scalar(
        select(Product)
        .options(selectinload(Product.documents))
        .where(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    existing = db.scalar(
        select(Product).where(Product.sku == payload.sku)
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists",
        )

    product = Product(**payload.model_dump(mode="json"))

    db.add(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists",
        )

    db.refresh(product)

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    updates = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    if "sku" in updates:
        existing = db.scalar(
            select(Product).where(
                Product.sku == updates["sku"],
                Product.id != product_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Product SKU already exists",
            )

    for field, value in updates.items():
        setattr(product, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Product SKU already exists",
        )

    db.refresh(product)

    return product


@router.delete("/{product_id}")
def deactivate_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    product.is_active = False
    db.commit()

    return {
        "message": "Product deactivated successfully"
    }
