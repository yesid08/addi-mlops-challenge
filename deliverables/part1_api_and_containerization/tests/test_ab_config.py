"""Tests for POST/GET/DELETE /ab/config endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def client(app_with_mock_graph):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mock_graph),
        base_url="http://test",
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_get_config_defaults(client):
    """GET /ab/config returns env-var defaults when no override is set."""
    response = await client.get("/ab/config")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "env_var"
    assert isinstance(data["traffic_pct"], int)
    assert isinstance(data["salt"], str)


@pytest.mark.asyncio
async def test_post_config_sets_override(client):
    """POST /ab/config stores the override and GET reflects it."""
    response = await client.post("/ab/config", json={"traffic_pct": 30})
    assert response.status_code == 200
    data = response.json()
    assert data["traffic_pct"] == 30
    assert data["source"] == "override"

    # GET should now return the same override
    get_response = await client.get("/ab/config")
    assert get_response.json()["traffic_pct"] == 30
    assert get_response.json()["source"] == "override"


@pytest.mark.asyncio
async def test_post_config_with_custom_salt(client):
    """POST /ab/config accepts a custom salt and returns it."""
    response = await client.post(
        "/ab/config", json={"traffic_pct": 50, "salt": "new-experiment-v2"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["traffic_pct"] == 50
    assert data["salt"] == "new-experiment-v2"
    assert data["source"] == "override"


@pytest.mark.asyncio
async def test_post_config_validation_above_100(client):
    """POST /ab/config rejects traffic_pct > 100 with 422."""
    response = await client.post("/ab/config", json={"traffic_pct": 101})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_config_validation_below_0(client):
    """POST /ab/config rejects traffic_pct < 0 with 422."""
    response = await client.post("/ab/config", json={"traffic_pct": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_config_boundary_zero(client):
    """POST /ab/config accepts traffic_pct=0 (kill-switch — all traffic to A)."""
    response = await client.post("/ab/config", json={"traffic_pct": 0})
    assert response.status_code == 200
    assert response.json()["traffic_pct"] == 0


@pytest.mark.asyncio
async def test_post_config_boundary_hundred(client):
    """POST /ab/config accepts traffic_pct=100 (all traffic to B)."""
    response = await client.post("/ab/config", json={"traffic_pct": 100})
    assert response.status_code == 200
    assert response.json()["traffic_pct"] == 100


@pytest.mark.asyncio
async def test_delete_config_reverts_to_env_var(client):
    """DELETE /ab/config clears overrides and reverts to env-var source."""
    # Set an override first
    await client.post("/ab/config", json={"traffic_pct": 75})
    assert (await client.get("/ab/config")).json()["source"] == "override"

    # Clear it
    response = await client.delete("/ab/config")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "env_var"


@pytest.mark.asyncio
async def test_kill_switch_routes_all_to_variant_a(client):
    """traffic_pct=0 means all /chat requests get variant A."""
    await client.post("/ab/config", json={"traffic_pct": 0})

    # All 8 valid users should be routed to A
    for i in range(1, 9):
        user_id = f"user_{i:03d}"
        response = await client.post(
            "/chat",
            json={
                "user_id": user_id,
                "conversation_id": f"conv-killswitch-{i}",
                "message": "hola",
            },
        )
        assert response.status_code == 200
        assert response.json()["ab_variant"] == "A", f"{user_id} should be variant A"


@pytest.mark.asyncio
async def test_full_treatment_routes_all_to_variant_b(client):
    """traffic_pct=100 means all /chat requests get variant B."""
    await client.post("/ab/config", json={"traffic_pct": 100})

    for i in range(1, 9):
        user_id = f"user_{i:03d}"
        response = await client.post(
            "/chat",
            json={
                "user_id": user_id,
                "conversation_id": f"conv-allb-{i}",
                "message": "hola",
            },
        )
        assert response.status_code == 200
        assert response.json()["ab_variant"] == "B", f"{user_id} should be variant B"
