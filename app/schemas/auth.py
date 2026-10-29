
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# ==========================================
# ADMIN AUTHENTICATION
# ==========================================

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==========================================
# CUSTOMER AUTHENTICATION
# ==========================================

class CustomerRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Name must contain at least 2 characters"
            )

        return value


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime


class CustomerTokenResponse(TokenResponse):
    customer: CustomerResponse
