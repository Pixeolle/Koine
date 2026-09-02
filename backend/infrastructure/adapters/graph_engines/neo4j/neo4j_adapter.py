from typing import Any

from neo4j import GraphDatabase
from neomodel import NodeSet, get_config, db
from loguru import logger

from backend.application.ports.graph_engine import GraphEngine
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.enums.dependency_type import DependencyType
from backend.domain.exceptions.id_already_inserted import IdAlreadyInserted
from backend.infrastructure.adapters.graph_engines.neo4j.code_node_entity import CodeNodeEntity
from backend.infrastructure.adapters.graph_engines.neo4j.code_node_entity_mapper import CodeNodeEntityMapper


class Neo4jAdapter(GraphEngine):

    def __init__(self, host: str, port: int):
        self.config = get_config()
        self.config.update(database_url=f'bolt://neo4j:neo4j@{host}:{port}')

        self._all_children_by_node_by_graph: dict[str, dict[CodeNode, list[CodeNode]] | None] = {}
        self._all_parents_by_node_by_graph: dict[str, dict[CodeNode, list[CodeNode]] | None ] = {}

    def populate(self, code_nodes: list[CodeNode], dependency_edges: list[DependencyEdge]):
        self.add_nodes(code_nodes)
        self.add_edges(dependency_edges)
        return

    def get_all_parents_by_node_by_graph(self, graph_id: str) -> dict[CodeNode, list[CodeNode]]:
        if self._all_parents_by_node_by_graph.get(graph_id, None) is None:
            self._compute_all_parents_by_node_for_graph_id(graph_id)

        all_parents_by_node = self._all_parents_by_node_by_graph[graph_id]
        assert all_parents_by_node is not None
        return all_parents_by_node

    def get_all_children_by_node_by_graph(self, graph_id: str) -> dict[CodeNode, list[CodeNode]]:
        if self._all_children_by_node_by_graph.get(graph_id, None) is None:
            self._compute_all_children_by_node_for_graph_id(graph_id)

        all_children_by_node = self._all_children_by_node_by_graph[graph_id]
        assert all_children_by_node is not None
        return all_children_by_node

    def update_node(self, code_node: CodeNode) -> None:
        node_entity = CodeNodeEntity.nodes.get(code_node_id=code_node.id)
        new_code_node_entity = CodeNodeEntityMapper.to_entity(code_node)
        node_entity.code_block = new_code_node_entity.code_block
        node_entity.llm_synthesis = new_code_node_entity.llm_synthesis
        node_entity.save()
        return

    def get_node(self, graph_id: str, node_id: str) -> CodeNode | None:
        try:
            entity = CodeNodeEntity.nodes.get(graph_id=graph_id, code_node_id=node_id)
        except Exception as _:
            return None
        return CodeNodeEntityMapper.to_domain(entity)

    def get_nodes(self, graph_id: str) -> list[CodeNode]:
        return [CodeNodeEntityMapper.to_domain(entity) for entity in CodeNodeEntity.nodes.filter(graph_id=graph_id)]

    def get_root_nodes(self, graph_id: str) -> list[CodeNode]:
        root_nodes: list[CodeNodeEntity] = list(CodeNodeEntity.nodes
        .filter(graph_id=graph_id)
        .has(is_called_by=False, is_contained_by=False))
        return [CodeNodeEntityMapper.to_domain(root_node) for root_node in root_nodes]

    def get_children_from_node_id(self, node_id: str) -> list[CodeNode]:
        return self._get_children_from_node_id(node_id)

    def get_children_from_node(self, node: CodeNode) -> list[CodeNode]:
        return self._get_children_from_node_id(node.id)

    def _get_children_from_node_id(self, node_id: str) -> list[CodeNode]:
        node_entity = CodeNodeEntity.nodes.get(code_node_id=node_id)
        children: set[CodeNodeEntity] = set(node_entity.contain.all())
        calls: set[CodeNodeEntity] = set(node_entity.call.all())
        return [CodeNodeEntityMapper.to_domain(code_node) for code_node in children | calls]

    def get_parent_from_node_id(self, node_id: str, filter_by_relation: Any = None) -> list[CodeNode]:
        return self._get_parent_from_node_id(
            node_id=node_id,
            filter_by_relation=filter_by_relation
        )

    def get_parent_from_node(self, node: CodeNode, filter_by_relation: Any = None) -> list[CodeNode]:
        return self._get_parent_from_node_id(
            node_id=node.id,
            filter_by_relation=filter_by_relation
        )

    def _get_parent_from_node_id(self, node_id: str, filter_by_relation: Any = None) -> list[CodeNode]:
        if not isinstance(filter_by_relation, DependencyType) and filter_by_relation is not None:
            return []

        node_entity = CodeNodeEntity.nodes.get(code_node_id=node_id)

        if filter_by_relation is DependencyType.CALL:
            return [CodeNodeEntityMapper.to_domain(code_node) for code_node in node_entity.is_called_by.all()]

        if filter_by_relation is DependencyType.STRUCTURAL:
            return [CodeNodeEntityMapper.to_domain(code_node) for code_node in node_entity.is_contained_by.all()]

        parents = set(node_entity.is_contained_by.all())
        calls = set(node_entity.is_called_by.all())
        return [CodeNodeEntityMapper.to_domain(code_node) for code_node in parents | calls]

    def add_nodes(self, nodes: list[CodeNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def add_node(self, node: CodeNode) -> None:
        nodes_already_inserted = list(CodeNodeEntity.nodes.filter(code_node_id=node.id))
        if len(nodes_already_inserted) > 0:
            raise IdAlreadyInserted(node.id)

        self._all_children_by_node_by_graph[node.graph_id] = None
        self._all_parents_by_node_by_graph[node.graph_id] = None
        CodeNodeEntityMapper.to_entity(node).save()

    def add_edges(self, edges: list[DependencyEdge]) -> None:
        for edge in edges:
            self.add_edge(edge)

        return

    def add_edge(self, edge: DependencyEdge) -> None:
        if edge.to_node_id == edge.from_node_id:
            return

        source_node: CodeNodeEntity = CodeNodeEntity.nodes.get(code_node_id=edge.from_node_id)
        destination_node: CodeNodeEntity = CodeNodeEntity.nodes.get(code_node_id=edge.to_node_id)

        self._all_children_by_node_by_graph[source_node.graph_id] = None
        self._all_parents_by_node_by_graph[source_node.graph_id] = None

        self._all_children_by_node_by_graph[destination_node.graph_id] = None
        self._all_parents_by_node_by_graph[destination_node.graph_id] = None

        if edge.type is DependencyType.CALL:
            source_node.call.connect(destination_node)
        if edge.type is DependencyType.STRUCTURAL:
            source_node.contain.connect(destination_node)
        return

    def _compute_all_parents_by_node_for_graph_id(self, graph_id: str) -> None:
        self._all_parents_by_node_by_graph[graph_id] = {}

        nodes: NodeSet = CodeNodeEntity.nodes.filter(graph_id=graph_id)

        for node in nodes:
            domain_node = CodeNodeEntityMapper.to_domain(node)

            parents = set(node.is_contained_by.all())
            calls = set(node.is_called_by.all())
            domain_parents = [CodeNodeEntityMapper.to_domain(code_node) for code_node in parents | calls]

            self._all_parents_by_node_by_graph[graph_id][domain_node] = domain_parents

        return

    def _compute_all_children_by_node_for_graph_id(self, graph_id: str) -> None:
        self._all_children_by_node_by_graph[graph_id] = {}

        nodes: NodeSet = CodeNodeEntity.nodes.filter(graph_id=graph_id)

        for node in nodes:
            domain_node = CodeNodeEntityMapper.to_domain(node)

            children = set(node.contain.all())
            calls = set(node.call.all())
            domain_children = [CodeNodeEntityMapper.to_domain(code_node) for code_node in children | calls]

            self._all_children_by_node_by_graph[graph_id][domain_node] = domain_children

        return

    def count_root_nodes(self, graph_id: str) -> int:
        return len(CodeNodeEntity.nodes
        .filter(graph_id=graph_id)
        .has(is_called_by=False, is_contained_by=False))

    def count_nodes(self, graph_id: str) -> int:
        return len(CodeNodeEntity.nodes.filter(graph_id=graph_id))

    def delete_graph(self, graph_id: str, batch_size: int = 5_000) -> None:
        db.cypher_query(
            f"""
            USING PERIODIC COMMIT {batch_size}
            MATCH (n:CodeNode {{graph_id: $graph_id}})
            DETACH DELETE n
            """,
            {"graph_id": graph_id}
        )
        return