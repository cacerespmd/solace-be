
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Admin
from app.core.security import hash_password


def seed_admin():
    with SessionLocal() as db:
        email = "solace@yopmail.com"

        existing_admin = db.scalar(
            select(Admin).where(Admin.email == email)
        )

        if existing_admin:
            print("SOLACE admin already exists. Skipping.")
            return

        admin = Admin(
            name="Solace Admin",
            email=email,
            password_hash=hash_password("Password123!"),
        )

        db.add(admin)
        db.commit()

        print("SOLACE default admin created successfully!")


if __name__ == "__main__":
    seed_admin()
