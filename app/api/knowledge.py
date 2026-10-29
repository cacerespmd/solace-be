import logging
import httpx

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.ai.knowledge import ingest_product_document
from app.core.dependencies import get_current_admin
from app.database import get_db
from app.models import Admin, Product, ProductDocument

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/knowledge",
    tags=["AI Knowledge Management"],
)


@router.post("/documents/{document_id}/ingest")
def ingest_document(
    document_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    document = db.get(ProductDocument, document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Product document not found",
        )

    product = db.get(Product, document.product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Associated product not found",
        )

    try:
        return ingest_product_document(
            document,
            product,
        )

    except (ValueError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except OpenAIError:
        logger.exception("OpenAI embedding request failed")

        raise HTTPException(
            status_code=503,
            detail="Embedding service is temporarily unavailable",
        )
