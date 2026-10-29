
import subprocess
import sys

from sqlalchemy import inspect

import app.models
from app.database import Base, engine


def initialize_database():
    print("Checking SOLACE database...")

    existing_tables = set(inspect(engine).get_table_names())
    required_tables = set(Base.metadata.tables.keys())

    is_new_database = not required_tables.intersection(existing_tables)

    print("Creating missing tables...")
    Base.metadata.create_all(bind=engine)

    if is_new_database:
        print("New database detected. Running seeders...")

        subprocess.run(
            [sys.executable, "-m", "app.seed"],
            check=True,
        )
    else:
        print("Existing database detected. Skipping seeders.")

    print("SOLACE database initialization completed!")


if __name__ == "__main__":
    initialize_database()
