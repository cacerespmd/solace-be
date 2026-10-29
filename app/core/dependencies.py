
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import Admin, Customer


bearer_scheme = HTTPBearer()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("role") != "admin":
            raise unauthorized

        admin_id = int(payload["sub"])

    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise unauthorized

    admin = db.get(Admin, admin_id)

    if admin is None:
        raise unauthorized

    return admin


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Customer:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired customer authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("role") != "customer":
            raise unauthorized

        customer_id = int(payload["sub"])

    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise unauthorized

    customer = db.get(Customer, customer_id)

    if customer is None:
        raise unauthorized

    return customer
