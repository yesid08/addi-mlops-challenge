import pytest


@pytest.mark.asyncio
async def test_health_returns_200(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_schema(async_client):
    response = await async_client.get("/health")
    data = response.json()
    assert "status" in data
    assert "graph_compiled" in data
    assert "openai_key_configured" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_status_ok_when_graph_ready(async_client):
    response = await async_client.get("/health")
    data = response.json()
    # graph is mocked as a non-None object, OPENAI_API_KEY is set in conftest
    assert data["graph_compiled"] is True
    assert data["openai_key_configured"] is True
    assert data["status"] == "ok"
