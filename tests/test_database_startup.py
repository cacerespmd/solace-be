from unittest.mock import Mock

from sqlalchemy import create_engine, inspect, select

import init_db
from app.database import Base
from app.models import Admin


def test_repeated_startup_preserves_rows_and_creates_missing_tables(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'startup.db'}")
    monkeypatch.setattr(init_db, "engine", engine)
    run_seeders = Mock()
    monkeypatch.setattr(init_db.subprocess, "run", run_seeders)

    try:
        # An existing database may have data but lack newer application tables.
        Admin.__table__.create(engine)
        with engine.begin() as connection:
            connection.execute(Admin.__table__.insert().values(
                name="Existing admin",
                email="existing@example.com",
                password_hash="existing-password-hash",
            ))
            original_rows = connection.execute(select(Admin.__table__)).all()

        for _ in range(2):
            init_db.initialize_database()
            with engine.connect() as connection:
                assert connection.execute(select(Admin.__table__)).all() == original_rows

        assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
        run_seeders.assert_not_called()
    finally:
        engine.dispose()
