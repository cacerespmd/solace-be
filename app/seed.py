
from scripts.seed_admin import seed_admin
from scripts.seed_customer import seed_customers
from scripts.seed_products import seed_products


def seed_database():
    print("\nSeeding SOLACE database...\n")

    seeders = [
        seed_admin,
        seed_customers,
        seed_products,
    ]

    for seeder in seeders:
        print(f"Running {seeder.__name__}...")
        seeder()

    print("\nSOLACE database seeded successfully!")


if __name__ == "__main__":
    seed_database()
