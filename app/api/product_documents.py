import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai.knowledge import ingest_product_document
from app.models import Admin, Product, ProductDocument
from app.core.dependencies import get_current_admin
from app.schemas.product_document import (
    ProductDocumentCreate,
    ProductDocumentUpdate,
    ProductDocumentResponse,
)


logger = logging.getLogger(__name__)


def index_document(document, product, db):
    """Only report a successful save after the submitted link is indexed."""
    try:
        ingest_product_document(document, product)
    except (ValueError, httpx.HTTPError) as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OpenAIError as exc:
        db.rollback()
        logger.exception("Document embedding request failed")
        raise HTTPException(
            status_code=503,
            detail="Document could not be indexed. Please try again.",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Document indexing failed")
        raise HTTPException(
            status_code=503,
            detail="Document could not be indexed. Please try again.",
        ) from exc


router = APIRouter(
    prefix="/api/products",
    tags=["Product Documents"],
)


@router.get(
    "/{product_id}/documents",
    response_model=list[ProductDocumentResponse],
)
def list_product_documents(
    product_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return db.scalars(
        select(ProductDocument)
        .where(ProductDocument.product_id == product_id)
        .order_by(ProductDocument.id.desc())
    ).all()


@router.post(
    "/{product_id}/documents",
    response_model=ProductDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_document(
    product_id: int,
    payload: ProductDocumentCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    product = db.get(Product, product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    document = ProductDocument(
        product_id=product_id,
        **payload.model_dump(mode="json"),
    )

    db.add(document)
    db.flush()
    index_document(document, product, db)
    db.commit()
    db.refresh(document)

    return document


@router.patch(
    "/{product_id}/documents/{document_id}",
    response_model=ProductDocumentResponse,
)
def update_product_document(
    product_id: int,
    document_id: int,
    payload: ProductDocumentUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    document = db.scalar(
        select(ProductDocument).where(
            ProductDocument.id == document_id,
            ProductDocument.product_id == product_id,
        )
    )

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    updates = payload.model_dump(exclude_unset=True, mode="json")

    for field, value in updates.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )
        setattr(document, field, value)

    if updates:
        product = db.get(Product, product_id)
        if product is None:
            db.rollback()
            raise HTTPException(status_code=404, detail="Product not found")
        index_document(document, product, db)

    db.commit()
    db.refresh(document)

    return document


@router.delete("/{product_id}/documents/{document_id}")
def delete_product_document(
    product_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    document = db.scalar(
        select(ProductDocument).where(
            ProductDocument.id == document_id,
            ProductDocument.product_id == product_id,
        )
    )

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(document)
    db.commit()

    return {"message": "Product document deleted successfully"}
