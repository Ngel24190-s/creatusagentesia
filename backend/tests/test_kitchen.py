"""Kitchen module tests."""
import pytest


@pytest.mark.asyncio
async def test_create_material(auth_client):
    resp = await auth_client.post(
        "/api/v1/kitchen/materials",
        json={"type": "horse_manure", "origin": "local_farm", "quantity_kg": 100.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "horse_manure"
    assert data["quantity_kg"] == 100.0


@pytest.mark.asyncio
async def test_list_materials(auth_client):
    resp = await auth_client.get("/api/v1/kitchen/materials")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_batch(auth_client):
    resp = await auth_client.post(
        "/api/v1/kitchen/batches",
        json={"code": "PRE-TEST-001", "recipe_details": {"mix": "50/50"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "PRE-TEST-001"
    assert data["status"] == "FERMENTING"
