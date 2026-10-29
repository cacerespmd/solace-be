
from scripts.seed_admin import seed_admin
from scripts.seed_customer  import seed_customers


def seed_database():
    print("\nSeeding SOLACE database...\n")

    seeders = [
        seed_admin,
        seed_customers,
    ]

    for seeder in seeders:
        print(f"Running {seeder.__name__}...")
        seeder()

    print("\nSOLACE database seeded successfully!")


if __name__ == "__main__":
    seed_database()
