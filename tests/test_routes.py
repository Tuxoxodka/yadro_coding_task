import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

graph_payload = {
    "name": "Test Graph",
    "nodes": [],
    "edges": [],
}

node_payload = {
    "name": "A",
}

edge_payload = {
    "from_node": "A",
    "to_node": "B",
}


@pytest.mark.asyncio
async def test_create_graph(async_client):
    response = await async_client.post("/api/graph/", json=graph_payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Test Graph"
    global graph_id
    graph_id = response.json()["id"]


@pytest.mark.asyncio
async def test_get_graph(async_client):
    response = await async_client.get(f"/api/graph/{graph_id}")
    assert response.status_code == 200
    assert response.json()["id"] == graph_id


@pytest.mark.asyncio
async def test_add_nodes(async_client):
    # Добавим два узла
    for suffix in ["A", "B"]:
        payload = {
            "name": suffix,
        }
        response = await async_client.post(f"/api/graph/{graph_id}/node/", json=payload)
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_nodes(async_client):
    response = await async_client.get(f"/api/graph/{graph_id}/nodes")
    assert response.status_code == 200
    nodes = response.json()
    assert len(nodes) == 2
    global node_ids
    node_ids = [node["id"] for node in nodes]


@pytest.mark.asyncio
async def test_add_edge(async_client):
    payload = {
        "from_node": "A",
        "to_node": "B",
    }
    response = await async_client.post(f"/api/graph/{graph_id}/edge/", json=payload)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_edges(async_client):
    response = await async_client.get(f"/api/graph/{graph_id}/edges")
    assert response.status_code == 200
    edges = response.json()
    assert len(edges) == 1


@pytest.mark.asyncio
async def test_get_adjacency_list(async_client):
    response = await async_client.get(f"/api/graph/{graph_id}/adjacency")
    assert response.status_code == 200
    data = response.json()
    assert "adjacency" in data
    assert isinstance(data["adjacency"], dict)


@pytest.mark.asyncio
async def test_get_transposed_adjacency_list(async_client):
    response = await async_client.get(f"/api/graph/{graph_id}/transposed")
    assert response.status_code == 200
    data = response.json()
    assert "adjacency" in data
    assert isinstance(data["adjacency"], dict)
