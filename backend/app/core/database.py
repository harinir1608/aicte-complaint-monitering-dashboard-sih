from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ── Engine ─────────────────────────────────────────────────────────────────────

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=not _is_sqlite,
    # SQLite uses StaticPool — pool_size/max_overflow not applicable
    **({} if _is_sqlite else {"pool_size": 10, "max_overflow": 20}),
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    echo=settings.is_development,
)


# Enable foreign-key enforcement for SQLite (used in tests)
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: object, _: object) -> None:
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ── Session factory ────────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Declarative base ───────────────────────────────────────────────────────────
# Import Base from models.base so that all ORM models share the same metadata.
# models.base does not import from app.core, so there is no circular dependency.
from app.models.base import Base  # noqa: E402, F401

# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """Yield a database session and guarantee it is closed afterward."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
