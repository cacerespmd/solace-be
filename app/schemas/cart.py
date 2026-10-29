
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AddCartItemRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1)


class CartProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    price: Decimal
    image_url: Optional[str] = None
    stock_quantity: int


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: CartProductResponse
    subtotal: Decimal


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    total_amount: Decimal
