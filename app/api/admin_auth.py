
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin
from app.schemas.auth import AdminLoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token


router = APIRouter(
    prefix="/api/admin/auth",
    tags=["Admin Authentication"]
)


@router.post("/login", response_model=TokenResponse)
def admin_login(
    payload: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    admin = db.scalar(
        select(Admin).where(
            Admin.email == str(payload.email).lower()
        )
    )

    if not admin or not verify_password(
        payload.password,
        admin.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return TokenResponse(
        access_token=create_access_token(admin.id)
    )
