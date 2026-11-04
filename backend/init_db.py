"""Create and verify all local SQLite tables for Chroma Context.

Run from the project root:
    backend\\venv\\Scripts\\python.exe backend\\init_db.py

The database path is defined in app/database.py and defaults to
backend/cvd_assistant.db. Existing data is preserved; create_all only creates
missing tables and does not delete or migrate existing records.
"""
from app import models  # Import all ORM models before create_all.
from app.database import engine, SQLALCHEMY_DATABASE_URL, Base
from sqlalchemy import inspect


def main() -> None:
    Base.metadata.create_all(bind=engine)
    tables = sorted(inspect(engine).get_table_names())
    expected = sorted(Base.metadata.tables.keys())
    missing = sorted(set(expected) - set(tables))
    print(f"Database: {SQLALCHEMY_DATABASE_URL}")
    print(f"Tables found: {len(tables)}")
    with engine.connect() as conn:
        for name in tables:
            count = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {name}").scalar()
            print(f"  [OK] {name:<24}: {count} records")
    if missing:
        raise SystemExit("Missing tables: " + ", ".join(missing))
    print("Database initialization/verification successful.")


if __name__ == "__main__":
    main()
