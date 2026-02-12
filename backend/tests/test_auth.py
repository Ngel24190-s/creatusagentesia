"""Auth endpoint tests."""
import pytest


@pytest.mark.asyncio
async def test_setup_creates_admin(client):
    resp = await client.post(
        "/api/v1/auth/setup",
        json={"username": "admin", "password": "SecurePass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_login_returns_token(client):
    await client.post(
        "/api/v1/auth/setup",
        json={"username": "admin2", "password": "SecurePass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin2", "password": "SecurePass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/setup",
        json={"username": "admin3", "password": "SecurePass123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin3", "password": "WrongPass"},
    )
    assert resp.status_code == 401
