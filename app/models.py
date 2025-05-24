from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Graph(Base):
    __tablename__ = "graphs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    # связи
    nodes = relationship("Node", back_populates="graph", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="graph", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    graph_id = Column(Integer, ForeignKey("graphs.id"))

    # связи
    graph = relationship("Graph", back_populates="nodes")
    outgoing = relationship(
        "Edge",
        back_populates="from_node",
        foreign_keys="Edge.from_node_id",
        cascade="all, delete-orphan"
    )
    incoming = relationship(
        "Edge",
        back_populates="to_node",
        foreign_keys="Edge.to_node_id",
        cascade="all, delete-orphan"
    )


class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True)
    from_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    to_node_id   = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    graph_id     = Column(Integer, ForeignKey("graphs.id"), nullable=False)

    # связи
    from_node = relationship(
        "Node",
        back_populates="outgoing",
        foreign_keys=[from_node_id]
    )
    to_node = relationship(
        "Node",
        back_populates="incoming",
        foreign_keys=[to_node_id]
    )
    graph = relationship("Graph", back_populates="edges")
