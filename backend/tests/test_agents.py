"""AI Agents tests."""
import pytest


@pytest.mark.asyncio
async def test_farm_health(auth_client):
    resp = await auth_client.get("/api/v1/agents/farm-health")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_score" in data
    assert "metrics" in data
    assert "alerts" in data
    assert 0 <= data["overall_score"] <= 100


@pytest.mark.asyncio
async def test_recommendations(auth_client):
    resp = await auth_client.get("/api/v1/agents/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_forecast(auth_client):
    resp = await auth_client.get("/api/v1/agents/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert "projections" in data


@pytest.mark.asyncio
async def test_ask_agent(auth_client):
    resp = await auth_client.post(
        "/api/v1/agents/ask",
        json={"question": "Que tal va la granja?"},
    )
    assert resp.status_code == 200
    assert "answer" in resp.json()
