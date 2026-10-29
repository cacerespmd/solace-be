
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Customer
from app.core.security import hash_password


def seed_customers():
    customers = [
        {
            "name": "John Doe",
            "email": "john.doe@yopmail.com",
            "password": "Password123!",
        },
        {
            "name": "Jane Doe",
            "email": "jane.doe@yopmail.com",
            "password": "Password123!",
        },
    ]

    with SessionLocal() as db:
        for customer_data in customers:
            existing_customer = db.scalar(
                select(Customer).where(
                    Customer.email == customer_data["email"]
                )
            )

            if existing_customer:
                print(
                    f"Customer {customer_data['name']} already exists. Skipping."
                )
                continue

            customer = Customer(
                name=customer_data["name"],
                email=customer_data["email"],
                password_hash=hash_password(
                    customer_data["password"]
                ),
            )

            db.add(customer)

            print(
                f"Customer {customer_data['name']} created successfully!"
            )

        db.commit()

    print("SOLACE customer seeding completed!")


if __name__ == "__main__":
    seed_customers()
