"""
Pytest fixtures for all tests.

Uses an in-memory SQLite database for full isolation.
Every test function gets a fresh database (create_all / drop_all).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so Base.metadata has every table registered
import app.models  # noqa: F401
from app.models.base import Base
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.models.bureau import Bureau
from app.models.complaint import ComplaintCategory
from app.models.institution import Institution
from app.models.user import User, UserRole

# ── In-memory SQLite engine (shared connection via StaticPool) ─────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    import sqlite3
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Core fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_db() -> Session:
    """Create all tables, yield a session, drop all tables after each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db: Session) -> TestClient:
    """TestClient with test_db injected via dependency override."""
    from app.main import app

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ── Bureau fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_bureau_rb(test_db: Session) -> Bureau:
    bureau = Bureau(code="RB", name="Regional Bureau", is_active=True)
    test_db.add(bureau)
    test_db.commit()
    test_db.refresh(bureau)
    return bureau


@pytest.fixture(scope="function")
def test_bureau_pgrc(test_db: Session) -> Bureau:
    bureau = Bureau(code="PGRC", name="PGRC Cell", is_active=True)
    test_db.add(bureau)
    test_db.commit()
    test_db.refresh(bureau)
    return bureau


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_admin(test_db: Session) -> User:
    user = User(
        email="testadmin@aicte.gov.in",
        hashed_password=hash_password("Admin@1234"),
        full_name="Test Admin",
        role=UserRole.system_admin,
        is_superuser=True,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_rb_officer(test_db: Session, test_bureau_rb: Bureau) -> User:
    user = User(
        email="testofficer.rb@aicte.gov.in",
        hashed_password=hash_password("Officer@1234"),
        full_name="Test RB Officer",
        role=UserRole.rb_officer,
        bureau_id=test_bureau_rb.id,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_pgrc_officer(test_db: Session, test_bureau_pgrc: Bureau) -> User:
    user = User(
        email="testofficer.pgrc@aicte.gov.in",
        hashed_password=hash_password("Officer@1234"),
        full_name="Test PGRC Officer",
        role=UserRole.pgrc_officer,
        bureau_id=test_bureau_pgrc.id,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ── Token fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def admin_token(test_admin: User) -> str:
    return create_access_token(
        user_id=test_admin.id,
        email=test_admin.email,
        role=test_admin.role,
    )


@pytest.fixture(scope="function")
def rb_officer_token(test_rb_officer: User) -> str:
    return create_access_token(
        user_id=test_rb_officer.id,
        email=test_rb_officer.email,
        role=test_rb_officer.role,
    )


@pytest.fixture(scope="function")
def pgrc_officer_token(test_pgrc_officer: User) -> str:
    return create_access_token(
        user_id=test_pgrc_officer.id,
        email=test_pgrc_officer.email,
        role=test_pgrc_officer.role,
    )


# ── Domain object fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_institution(test_db: Session) -> Institution:
    institution = Institution(
        name="Test Engineering College",
        permanent_id="TEST-001",
        state="Maharashtra",
        is_active=True,
    )
    test_db.add(institution)
    test_db.commit()
    test_db.refresh(institution)
    return institution


@pytest.fixture(scope="function")
def test_category(test_db: Session) -> ComplaintCategory:
    category = ComplaintCategory(
        code="FEE",
        name="Fee Related",
        description="Fee related complaints",
        default_sla_days=30,
    )
    test_db.add(category)
    test_db.commit()
    test_db.refresh(category)
    return category
