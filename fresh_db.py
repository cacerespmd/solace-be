import argparse
import subprocess
import sys

import app.models

from app.database import Base, engine


def fresh_database():
    print("\nDropping existing database tables...")
    Base.metadata.drop_all(bind=engine)

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    print("SOLACE database migrated successfully!")


def seed_database():
    subprocess.run(
        [sys.executable, "-m", "app.seed"],
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="SOLACE database migration and seeding."
    )

    parser.add_argument(
        "--seed",
        action="store_true",
        help="Run registered seeders after fresh migration.",
    )

    args = parser.parse_args()

    print("WARNING: All existing database records will be deleted.")

    confirmation = input("Type 'yes' to continue: ")

    if confirmation.strip().lower() != "yes":
        print("Operation cancelled.")
        return

    fresh_database()

    if args.seed:
        seed_database()

    print("\nSOLACE database setup completed!")


if __name__ == "__main__":
    main()