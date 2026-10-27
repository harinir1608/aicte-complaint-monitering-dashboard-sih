"""Tests for authentication endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


# ── Login tests ───────────────────────────────────────────────────────────────

def test_login_success(client: TestClient, test_admin: User):
    """Valid credentials return 200 with access and refresh tokens."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@aicte.gov.in", "password": "Admin@1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"]


def test_login_wrong_password(client: TestClient, test_admin: User):
    """Wrong password returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@aicte.gov.in", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Login for non-existent user returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@aicte.gov.in", "password": "Admin@1234"},
    )
    assert response.status_code == 401


# ── /me tests ─────────────────────────────────────────────────────────────────

def test_get_me_authenticated(client: TestClient, test_admin: User, admin_token: str):
    """Authenticated user can retrieve their own profile."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testadmin@aicte.gov.in"
    assert data["full_name"] == "Test Admin"
    assert data["role"] == "system_admin"


def test_get_me_unauthenticated(client: TestClient):
    """Request without token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


# ── Change password tests ─────────────────────────────────────────────────────

def test_change_password(client: TestClient, test_admin: User, admin_token: str):
    """User can change password when old password is correct."""
    response = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "Admin@1234", "new_password": "NewAdmin@5678"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "detail" in data

    # Verify new password works
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@aicte.gov.in", "password": "NewAdmin@5678"},
    )
    assert login_resp.status_code == 200


def test_change_password_wrong_old(client: TestClient, test_admin: User, admin_token: str):
    """Providing the wrong old password returns 400."""
    response = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "WrongOld@1234", "new_password": "NewAdmin@5678"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
