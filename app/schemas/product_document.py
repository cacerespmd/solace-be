
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProductDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    document_url: HttpUrl
    document_type: str = Field(default="manual", min_length=1, max_length=50)


class ProductDocumentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    document_url: Optional[HttpUrl] = None
    document_type: Optional[str] = Field(default=None, min_length=1, max_length=50)


class ProductDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    title: str
    document_url: str
    document_type: str
    created_at: datetime
