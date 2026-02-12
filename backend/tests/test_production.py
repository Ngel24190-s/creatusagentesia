"""Production module tests."""
import pytest


@pytest.mark.asyncio
async def test_create_ibc(auth_client):
    resp = await auth_client.post(
        "/api/v1/production/ibcs",
        json={"code": "IBC-TEST-001", "location": "Hangar A", "worm_biomass_kg": 5.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "IBC-TEST-001"
    assert data["worm_biomass_kg"] == 5.0


@pytest.mark.asyncio
async def test_list_ibcs(auth_client):
    resp = await auth_client.get("/api/v1/production/ibcs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_hungry_alerts(auth_client):
    resp = await auth_client.get("/api/v1/production/alerts/hungry-ibcs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
