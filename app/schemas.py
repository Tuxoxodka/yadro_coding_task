from typing import List, Dict
from pydantic import BaseModel, Field, constr


class NodeCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(..., example="A")


class EdgeCreate(BaseModel):
    from_node: str = Field(..., example="A")
    to_node: str = Field(..., example="B")


class GraphCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=255) = Field(..., example="MyGraph")
    nodes: List[NodeCreate] = []  #Field(default_factory=list)
    edges: List[EdgeCreate] = []  #Field(default_factory=list)


class NodeRead(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class EdgeRead(BaseModel):
    id: int
    from_node: str
    to_node: str

    model_config = {
        "from_attributes": True
    }


class GraphRead(BaseModel):
    id: int
    name: str
    nodes: List[NodeRead]
    edges: List[EdgeRead]

    model_config = {
        "from_attributes": True
    }


GraphOut = GraphRead

GraphDetail = GraphRead

NodeOut = NodeRead

EdgeOut = EdgeRead


class AdjacencyList(BaseModel):
    adjacency: Dict[str, List[str]]
