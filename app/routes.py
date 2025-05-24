from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from database import get_db
import schemas
import services

graph_router = APIRouter()

# ГРАФЫ


@graph_router.post("/graph/", response_model=schemas.GraphOut, status_code=status.HTTP_201_CREATED)
def create_graph(graph_in: schemas.GraphCreate, db: Session = Depends(get_db)):
    return services.create_graph(db, graph_in)

@graph_
router.get("/graph/{graph_id}", response_model=schemas.GraphDetail)
def get_graph(graph_id: int, db: Session = Depends(get_db)):
    return services.get_graph_details(db, graph_id)

# ВЕРШИНЫ


@graph_router.post("/graph/{graph_id}/node/", response_model=schemas.NodeOut, status_code=status.HTTP_201_CREATED)
def add_node(graph_id: int, node_in: schemas.NodeCreate, db: Session = Depends(get_db)):
    return services.add_node(db, graph_id, node_in)


@graph_router.get("/graph/{graph_id}/nodes", response_model=list[schemas.NodeOut])
def list_nodes(graph_id: int, db: Session = Depends(get_db)):
    return services.get_nodes(db, graph_id)

# РЁБРА


@graph_router.post("/graph/{graph_id}/edge/", response_model=schemas.EdgeOut, status_code=status.HTTP_201_CREATED)
def add_edge(graph_id: int, edge_in: schemas.EdgeCreate, db: Session = Depends(get_db)):
    return services.add_edge(db, graph_id, edge_in)


@graph_router.get("/graph/{graph_id}/edges", response_model=list[schemas.EdgeOut])
def list_edges(graph_id: int, db: Session = Depends(get_db)):
    return services.get_edges(db, graph_id)

# ПРЕДСТАВЛЕНИЕ ГРАФА


@graph_router.get("/graph/{graph_id}/adjacency", response_model=schemas.AdjacencyList)
def get_adjacency_list(graph_id: int, db: Session = Depends(get_db)):
    return services.get_adjacency_list(db, graph_id)


@graph_router.get("/graph/{graph_id}/transposed", response_model=schemas.AdjacencyList)
def get_transposed_adjacency_list(graph_id: int, db: Session = Depends(get_db)):
    return services.get_transposed_adjacency_list(db, graph_id)
