from typing import List, Dict
from pydantic import BaseModel, Field, constr


class NodeCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(..., example="A")


class EdgeCreate(BaseModel):
    from_node: str = Field(..., example="A")
    to_node: str = Field(..., example="B")


class GraphCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(..., example="MyGraph")
    nodes: List[NodeCreate]
    edges: List[EdgeCreate]


class NodeRead(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class EdgeRead(BaseModel):
    id: int
    from_node: str
    to_node: str

    class Config:
        orm_mode = True


class GraphRead(BaseModel):
    id: int
    name: str
    nodes: List[NodeRead]
    edges: List[EdgeRead]

    class Config:
        orm_mode = True


GraphOut = GraphRead

GraphDetail = GraphRead

NodeOut = NodeRead

EdgeOut = EdgeRead


class AdjacencyList(BaseModel):
    adjacency: Dict[str, List[str]]
