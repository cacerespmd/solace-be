
from app.database import Base, engine

# Import all models so SQLAlchemy knows
# which tables need to be created.
import app.models


def create_database():
    print("Creating SOLACE database tables...")

    Base.metadata.create_all(bind=engine)

    print("SOLACE database tables created successfully!")


if __name__ == "__main__":
    create_database()
