
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatSource(BaseModel):
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    document_id: Optional[int] = None
    document_title: Optional[str] = None
    source_url: Optional[str] = None

class ChatProduct(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    sources: List[ChatSource] = Field(default_factory=list)
    products: List[ChatProduct] = []

