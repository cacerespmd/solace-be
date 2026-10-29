
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class ProductDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    title: str
    document_url: str
    document_type: str
    created_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    sku: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None

    price: Decimal = Field(
        ge=0,
        max_digits=10,
        decimal_places=2,
    )

    stock_quantity: int = Field(default=0, ge=0)
    image_url: Optional[HttpUrl] = None

    @field_validator("name", "sku")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=150,
    )
    sku: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    description: Optional[str] = None

    price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    )

    stock_quantity: Optional[int] = Field(default=None, ge=0)
    image_url: Optional[HttpUrl] = None
    is_active: Optional[bool] = None

    @field_validator("name", "sku")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @model_validator(mode="after")
    def validate_required_fields(self):
        required_fields = {
            "name",
            "sku",
            "price",
            "stock_quantity",
            "is_active",
        }

        for field in required_fields:
            if field in self.model_fields_set:
                if getattr(self, field) is None:
                    raise ValueError(f"{field} cannot be null")

        return self


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    description: Optional[str]
    price: Decimal
    stock_quantity: int
    image_url: Optional[str]
    is_active: bool

    documents: List[ProductDocumentResponse] = Field(
        default_factory=list
    )
