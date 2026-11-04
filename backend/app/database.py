"""
DB engine/session setup.

For local development we use SQLite so the project runs with zero setup.
In production (per the architecture diagram) this swaps for Amazon DynamoDB --
swap SQLALCHEMY_DATABASE_URL for a real Postgres/RDS URL, or replace this
module with a boto3 DynamoDB client, without touching models.py's field
names (they already match the ER diagram's DynamoDB-style attribute names).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Always store the SQLite file next to the backend folder, no matter which
# directory uvicorn is started from. (A relative path used to silently create
# a fresh, empty database whenever the server was launched from elsewhere,
# which made registered users "disappear" and logins fail.)
_DB_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "cvd_assistant.db")
)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + _DB_FILE.replace("\\", "/"))

connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
