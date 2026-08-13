from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

from sqlalchemy.event import listens_for

# Single-threaded SQLite engine configuration with WAL journal mode for 10x concurrency performance
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

@listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enables SQLite Write-Ahead Logging (WAL) mode for fast concurrent operations."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency provider yielding database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
