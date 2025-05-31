from sqlalchemy.orm import Session
from fastapi import HTTPException, status

import app.schemas as schemas
from app.models import Graph, Node, Edge
from app.schemas import GraphCreate, NodeCreate, EdgeCreate

from collections import defaultdict, deque


def create_graph(db: Session, graph_data: GraphCreate) -> Graph:
    # Проверка на уникальность имён вершин внутри графа
    node_names = set()
    for node in graph_data.nodes:
        if node.name in node_names:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate node name '{node.name}' in the same graph."
            )
        node_names.add(node.name)

    # Создаём граф
    graph = Graph(name=graph_data.name)
    db.add(graph)
    db.flush()  # Чтобы получить graph.id

    # Создаём вершины
    node_objs = {}
    for node in graph_data.nodes:
        node_obj = Node(name=node.name, graph_id=graph.id)
        db.add(node_obj)
        node_objs[node.name] = node_obj

    db.flush()  # Чтобы получить node.id

    # Проверка на дубликаты рёбер и формирование объектов
    edge_set = set()
    edge_objs = []
    for edge in graph_data.edges:
        key = (edge.from_node, edge.to_node)
        if key in edge_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate edge from '{edge.from_node}' to '{edge.to_node}'."
            )
        edge_set.add(key)

        if edge.from_node not in node_objs or edge.to_node not in node_objs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid edge: node '{edge.from_node}' or '{edge.to_node}' not found."
            )

        edge_objs.append(
            Edge(
                from_node_id=node_objs[edge.from_node].id,
                to_node_id=node_objs[edge.to_node].id,
                graph_id=graph.id
            )
        )

    # Проверка на ацикличность
    if not is_acyclic(graph_data.nodes, graph_data.edges):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Graph must be acyclic (DAG)."
        )

    # Сохраняем рёбра и возвращаем граф
    db.add_all(edge_objs)
    db.commit()
    db.refresh(graph)
    db.expire_all()
    return graph


def get_graph_details(db: Session, graph_id: int) -> schemas.GraphRead:
    # Получаем граф и связанные вершины/рёбра
    graph = db.query(Graph).filter_by(id=graph_id).first()
    if not graph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    nodes = db.query(Node).filter_by(graph_id=graph_id).all()
    edges = db.query(Edge).filter_by(graph_id=graph_id).all()

    # Собираем словарь id->name
    id_to_name = {n.id: n.name for n in nodes}

    # Формируем схемы ответов
    nodes_read = [schemas.NodeRead.from_orm(n) for n in nodes]
    edges_read = [
        schemas.EdgeRead(
            id=e.id,
            from_node=id_to_name[e.from_node_id],
            to_node=id_to_name[e.to_node_id]
        )
        for e in edges
    ]

    return schemas.GraphRead(
        id=graph.id,
        name=graph.name,
        nodes=nodes_read,
        edges=edges_read
    )


def add_node(db: Session, graph_id: int, node_in: NodeCreate) -> schemas.NodeRead:
    # Проверка наличия графа
    graph = db.query(Graph).filter_by(id=graph_id).first()
    if not graph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    # Проверяем уникальность имени в графе
    exists = db.query(Node).filter_by(graph_id=graph_id, name=node_in.name).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node '{node_in.name}' already exists in graph {graph_id}."
        )

    node = Node(name=node_in.name, graph_id=graph_id)
    db.add(node)
    db.commit()
    db.refresh(node)
    return schemas.NodeRead.from_orm(node)


def get_nodes(db: Session, graph_id: int) -> list[schemas.NodeRead]:
    # Проверка наличия графа
    if not db.query(Graph).filter_by(id=graph_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    nodes = db.query(Node).filter_by(graph_id=graph_id).all()
    return [schemas.NodeRead.from_orm(n) for n in nodes]


def add_edge(db: Session, graph_id: int, edge_in: EdgeCreate) -> schemas.EdgeRead:
    # Проверка наличия графа
    if not db.query(Graph).filter_by(id=graph_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    # Проверка существования вершин
    nodes = db.query(Node).filter_by(graph_id=graph_id).all()
    id_to_name = {n.id: n.name for n in nodes}
    name_to_id = {n.name: n.id for n in nodes}

    if edge_in.from_node not in name_to_id or edge_in.to_node not in name_to_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"One or both nodes '{edge_in.from_node}', '{edge_in.to_node}' do not exist."
        )

    # Проверка дубликата ребра
    exists = db.query(Edge).filter_by(
        graph_id=graph_id,
        from_node_id=name_to_id[edge_in.from_node],
        to_node_id=name_to_id[edge_in.to_node]
    ).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Edge from '{edge_in.from_node}' to '{edge_in.to_node}' already exists."
        )

    # Проверка на ацикличность: собираем все существующие + новое ребро
    node_creates = [NodeCreate(name=n.name) for n in nodes]
    edge_creates = [
        EdgeCreate(from_node=id_to_name[e.from_node_id], to_node=id_to_name[e.to_node_id])
        for e in db.query(Edge).filter_by(graph_id=graph_id).all()
    ]
    edge_creates.append(edge_in)

    if not is_acyclic(node_creates, edge_creates):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adding this edge would create a cycle."
        )

    # Сохраняем ребро
    edge = Edge(
        from_node_id=name_to_id[edge_in.from_node],
        to_node_id=name_to_id[edge_in.to_node],
        graph_id=graph_id
    )
    db.add(edge)
    db.commit()
    db.refresh(edge)

    return schemas.EdgeRead(
        id=edge.id,
        from_node=edge_in.from_node,
        to_node=edge_in.to_node
    )


def get_edges(db: Session, graph_id: int) -> list[schemas.EdgeRead]:
    # Проверка наличия графа
    if not db.query(Graph).filter_by(id=graph_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    edges = db.query(Edge).filter_by(graph_id=graph_id).all()
    # Собираем id->name для вершин
    nodes = db.query(Node).filter_by(graph_id=graph_id).all()
    id_to_name = {n.id: n.name for n in nodes}

    return [
        schemas.EdgeRead(
            id=e.id,
            from_node=id_to_name[e.from_node_id],
            to_node=id_to_name[e.to_node_id]
        )
        for e in edges
    ]


def get_adjacency_list(db: Session, graph_id: int) -> schemas.AdjacencyList:
    # Проверка наличия графа
    if not db.query(Graph).filter_by(id=graph_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    nodes = db.query(Node).filter_by(graph_id=graph_id).all()
    edges = db.query(Edge).filter_by(graph_id=graph_id).all()
    # Инициализируем словарь
    adj: dict[str, list[str]] = {n.name: [] for n in nodes}
    for e in edges:
        from_name = next(n.name for n in nodes if n.id == e.from_node_id)
        adj[from_name].append(next(n.name for n in nodes if n.id == e.to_node_id))

    return schemas.AdjacencyList(adjacency=adj)


def get_transposed_adjacency_list(db: Session, graph_id: int) -> schemas.AdjacencyList:
    # Проверка наличия графа
    if not db.query(Graph).filter_by(id=graph_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph not found")

    nodes = db.query(Node).filter_by(graph_id=graph_id).all()
    edges = db.query(Edge).filter_by(graph_id=graph_id).all()
    # Инициализируем словарь
    transposed: dict[str, list[str]] = {n.name: [] for n in nodes}
    for e in edges:
        to_name = next(n.name for n in nodes if n.id == e.to_node_id)
        transposed[to_name].append(next(n.name for n in nodes if n.id == e.from_node_id))

    return schemas.AdjacencyList(adjacency=transposed)


def is_acyclic(nodes: list[NodeCreate], edges: list[EdgeCreate]) -> bool:
    """
    Алгоритм Кана для проверки DAG:
    - nodes: список NodeCreate с атрибутом name
    - edges: список EdgeCreate с атрибутами from_node и to_node
    """
    graph = defaultdict(list)
    indegree = defaultdict(int)

    # Инициализируем
    for node in nodes:
        graph[node.name] = []
        indegree[node.name] = 0

    # Строим граф
    for edge in edges:
        graph[edge.from_node].append(edge.to_node)
        indegree[edge.to_node] += 1

    # Собираем все с нулевой степенью входа
    queue = deque([n for n in graph if indegree[n] == 0])
    visited = 0

    while queue:
        current = queue.popleft()
        visited += 1
        for neighbor in graph[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # Если мы прошли все вершины — граф ацикличен
    return visited == len(nodes)
