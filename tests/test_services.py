import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app import schemas, services
from app.models import Graph, Node, Edge
from app.services import create_graph, get_graph_details, add_edge, add_node
import uuid


def test_create_graph_success(db_session: Session):
    graph_data = schemas.GraphCreate(
        name="TestGraph",
        nodes=[
            schemas.NodeCreate(name="A"),
            schemas.NodeCreate(name="B")
        ],
        edges=[
            schemas.EdgeCreate(from_node="A", to_node="B")
        ]
    )
    graph = create_graph(db_session, graph_data)
    assert isinstance(graph, Graph)
    assert graph.name == "TestGraph"


def test_create_graph_duplicate_nodes(db_session: Session):
    graph_data = schemas.GraphCreate(
        name="BadGraph",
        nodes=[
            schemas.NodeCreate(name="A"),
            schemas.NodeCreate(name="A")
        ],
        edges=[]
    )
    with pytest.raises(HTTPException) as exc:
        create_graph(db_session, graph_data)
    assert exc.value.status_code == 400
    assert "Duplicate node name" in exc.value.detail


def test_create_graph_duplicate_edges(db_session: Session):
    graph_data = schemas.GraphCreate(
        name="BadGraph2",
        nodes=[
            schemas.NodeCreate(name="A"),
            schemas.NodeCreate(name="B")
        ],
        edges=[
            schemas.EdgeCreate(from_node="A", to_node="B"),
            schemas.EdgeCreate(from_node="A", to_node="B")
        ]
    )
    with pytest.raises(HTTPException) as exc:
        create_graph(db_session, graph_data)
    assert exc.value.status_code == 400
    assert "Duplicate edge" in exc.value.detail


def test_create_graph_invalid_edge_nodes(db_session: Session):
    graph_data = schemas.GraphCreate(
        name="BadGraph3",
        nodes=[
            schemas.NodeCreate(name="A")
        ],
        edges=[
            schemas.EdgeCreate(from_node="A", to_node="B")
        ]
    )
    with pytest.raises(HTTPException) as exc:
        create_graph(db_session, graph_data)
    assert exc.value.status_code == 400
    assert "Invalid edge" in exc.value.detail


def test_get_graph_details_success(db_session: Session):
    graph_data = schemas.GraphCreate(
        name="GraphForRead",
        nodes=[
            schemas.NodeCreate(name="X"),
            schemas.NodeCreate(name="Y")
        ],
        edges=[
            schemas.EdgeCreate(from_node="X", to_node="Y")
        ]
    )
    graph = create_graph(db_session, graph_data)
    details = get_graph_details(db_session, graph.id)
    assert details.id == graph.id
    assert details.name == "GraphForRead"
    assert len(details.nodes) == 2
    assert len(details.edges) == 1


def test_get_graph_details_not_found(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        get_graph_details(db_session, 9999)
    assert exc.value.status_code == 404


@pytest.fixture
def graph(db_session):
    unique_name = f"TestGraph_{uuid.uuid4().hex[:8]}"
    graph_in = schemas.GraphCreate(name=unique_name, nodes=[], edges=[])
    graph = services.create_graph(db_session, graph_in)
    db_session.commit()
    db_session.refresh(graph)
    return graph


def test_add_node_success(db_session: Session, graph: Graph):
    node_in = schemas.NodeCreate(name="A")
    node_out = services.add_node(db_session, graph.id, node_in)

    assert node_out.name == "A"
    assert isinstance(node_out.id, int)


def test_add_node_graph_not_found(db_session: Session):
    node_in = schemas.NodeCreate(name="X")

    with pytest.raises(HTTPException) as e:
        services.add_node(db_session, graph_id=9999, node_in=node_in)

    assert e.value.status_code == 404
    assert "Graph not found" in e.value.detail


def test_add_node_duplicate(db_session: Session, graph: Graph):
    node_in = schemas.NodeCreate(name="B")
    services.add_node(db_session, graph.id, node_in)

    with pytest.raises(HTTPException) as e:
        services.add_node(db_session, graph.id, node_in)

    assert e.value.status_code == 400
    assert "already exists" in e.value.detail


def test_add_edge_success(db_session: Session, graph: Graph):
    node_a = services.add_node(db_session, graph.id, schemas.NodeCreate(name="A"))
    node_b = services.add_node(db_session, graph.id, schemas.NodeCreate(name="B"))

    edge_in = schemas.EdgeCreate(from_node="A", to_node="B")
    edge_out = services.add_edge(db_session, graph.id, edge_in)

    assert edge_out.from_node == "A"
    assert edge_out.to_node == "B"
    assert isinstance(edge_out.id, int)


def test_add_edge_graph_not_found(db_session: Session):
    edge_in = schemas.EdgeCreate(from_node="X", to_node="Y")

    with pytest.raises(HTTPException) as e:
        services.add_edge(db_session, graph_id=9999, edge_in=edge_in)

    assert e.value.status_code == 404
    assert "Graph not found" in e.value.detail


def test_add_edge_node_not_found(db_session: Session, graph: Graph):
    services.add_node(db_session, graph.id, schemas.NodeCreate(name="A"))

    edge_in = schemas.EdgeCreate(from_node="A", to_node="Z")

    with pytest.raises(HTTPException) as e:
        services.add_edge(db_session, graph.id, edge_in)

    assert e.value.status_code == 400
    assert "do not exist" in e.value.detail


def test_add_edge_duplicate(db_session: Session, graph: Graph):
    services.add_node(db_session, graph.id, schemas.NodeCreate(name="A"))
    services.add_node(db_session, graph.id, schemas.NodeCreate(name="B"))

    edge_in = schemas.EdgeCreate(from_node="A", to_node="B")
    services.add_edge(db_session, graph.id, edge_in)

    with pytest.raises(HTTPException) as e:
        services.add_edge(db_session, graph.id, edge_in)

    assert e.value.status_code == 400
    assert "already exists" in e.value.detail


def test_add_edge_creates_cycle(db_session: Session, graph: Graph):
    # A → B → C, try adding C → A
    services.add_node(db_session, graph.id, schemas.NodeCreate(name="A"))
    services.add_node(db_session, graph.id, schemas.NodeCreate(name="B"))
    services.add_node(db_session, graph.id, schemas.NodeCreate(name="C"))

    services.add_edge(db_session, graph.id, schemas.EdgeCreate(from_node="A", to_node="B"))
    services.add_edge(db_session, graph.id, schemas.EdgeCreate(from_node="B", to_node="C"))

    # цикл: C → A
    with pytest.raises(HTTPException) as e:
        services.add_edge(db_session, graph.id, schemas.EdgeCreate(from_node="C", to_node="A"))

    assert e.value.status_code == 400
    assert "create a cycle" in e.value.detail