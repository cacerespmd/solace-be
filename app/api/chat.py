
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.ai.service import generate_ai_response
from app.core.dependencies import get_current_customer
from app.database import get_db
from app.models import Customer
from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Customer Support"],
)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    try:
        result = generate_ai_response(
            message=payload.message,
            db=db,
            customer_id=customer.id,
        )

        return ChatResponse(
            reply=result["reply"],
            sources=result["sources"],
            products=result.get("products", []),
        )

    except OpenAIError:
        raise HTTPException(
            status_code=503,
            detail="AI support is temporarily unavailable",
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="AI support could not complete the request",
        )
