
from sqlalchemy import inspect, text
from app.database import engine

def check_database():
    print("\n========== SOLACE DATABASE CHECK ==========")
    print("Database URL:", engine.url.render_as_string(hide_password=True))

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if not tables:
        print("No tables found!")
        return

    with engine.connect() as connection:
        for table in tables:
            quoted_table = connection.dialect.identifier_preparer.quote(table)

            result = connection.execute(
                text(f"SELECT COUNT(*) FROM {quoted_table}")
            )
            count = result.scalar()

            print(f"Table: {table} | Records: {count}")

    print("===========================================\n")

if __name__ == "__main__":
    check_database()
