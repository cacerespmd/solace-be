
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.schemas.support_ticket import SupportTicketResponse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)


# ==========================================
# 1. CHECKOUT REQUEST
# ==========================================

class CheckoutRequest(BaseModel):
    recipient_name: str = Field(
        min_length=1,
        max_length=255
    )

    contact_number: str = Field(
        min_length=7,
        max_length=20
    )

    address_line_1: str = Field(
        min_length=1,
        max_length=255
    )

    address_line_2: Optional[str] = Field(
        default=None,
        max_length=255
    )

    barangay: str = Field(
        min_length=1,
        max_length=150
    )

    city: str = Field(
        min_length=1,
        max_length=150
    )

    province: str = Field(
        min_length=1,
        max_length=150
    )

    postal_code: str = Field(
        min_length=1,
        max_length=20
    )

    country: str = Field(
        default="Philippines",
        min_length=1,
        max_length=100
    )

    delivery_notes: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    @field_validator(
        "recipient_name",
        "contact_number",
        "address_line_1",
        "barangay",
        "city",
        "province",
        "postal_code",
        "country",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty"
            )

        return value

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, value: str) -> str:
        allowed = set("0123456789+-() ")

        if any(
            character not in allowed
            for character in value
        ):
            raise ValueError(
                "Invalid contact number format"
            )

        digits = "".join(
            character
            for character in value
            if character.isdigit()
        )

        if not 7 <= len(digits) <= 15:
            raise ValueError(
                "Contact number must contain 7 to 15 digits"
            )

        return value


# ==========================================
# 2. ORDER ITEM PRODUCT RESPONSE
# ==========================================

class OrderItemProductResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    name: str
    image_url: Optional[str] = None


# ==========================================
# 3. ORDER ITEM RESPONSE
# ==========================================

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    # Read the related Product model.
    # Exclude the nested object from JSON output.
    product: Optional[OrderItemProductResponse] = Field(
        default=None,
        exclude=True
    )

    @computed_field
    @property
    def product_name(self) -> Optional[str]:
        if self.product is None:
            return None

        return self.product.name

    @computed_field
    @property
    def product_image_url(self) -> Optional[str]:
        if self.product is None:
            return None

        return self.product.image_url


# ==========================================
# 4. ORDER DELIVERY RESPONSE
# ==========================================

class OrderDeliveryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    order_id: int

    # Recipient Information
    recipient_name: str
    contact_number: str

    # Shipping Address
    address_line_1: str
    address_line_2: Optional[str]

    barangay: str
    city: str
    province: str
    postal_code: str
    country: str

    delivery_notes: Optional[str]

    # Courier Information
    courier_name: Optional[str]
    tracking_number: Optional[str]

    # Delivery Status
    status: str

    # Delivery Timestamps
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    received_at: Optional[datetime]

    # Record Timestamps
    created_at: datetime
    updated_at: datetime


# ==========================================
# 5. ORDER RESPONSE
# ==========================================

class OrderResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    order_number: str
    status: str
    total_amount: Decimal
    created_at: datetime

    items: List[OrderItemResponse]

    delivery: Optional[OrderDeliveryResponse] = None
    support_tickets: List[SupportTicketResponse] = []