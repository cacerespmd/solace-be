
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TicketCategory = Literal[
    "general",
    "delivery_issue",
    "damaged_item",
    "wrong_item",
    "missing_item",
    "return_request",
    "refund_request",
    "cancellation_request",
]


class SupportTicketCreate(BaseModel):
    category: TicketCategory

    order_id: Optional[int] = Field(
        default=None,
        gt=0,
    )

    subject: str = Field(
        min_length=5,
        max_length=255,
    )

    description: str = Field(
        min_length=10,
        max_length=5000,
    )


class SupportTicketResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    customer_id: int
    order_id: Optional[int]
    category: str
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


class SupportTicketListResponse(BaseModel):
    tickets: List[SupportTicketResponse]
