from typing import Any

import rustworkx as rx

from backend.application.ports.graph_engine import GraphEngine
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.enums.dependency_type import DependencyType
from backend.domain.exceptions.id_already_inserted import IdAlreadyInserted
from backend.domain.exceptions.id_not_found import IdNotFound


class RustworkxAdapter(GraphEngine):
    def __init__(self):
        self._graph = rx.PyDiGraph()
        self._node_indices: dict[str, int] = {}
        self._node_id_to_graph_id: dict[str, str] = {}
        self._graph_id_to_node_indices: dict[str, list[int]] = {}
        self._all_children_by_node_by_graph: dict[str, dict[CodeNode, list[CodeNode]] | None ] = {}
        self._all_parent_by_node_by_graph: dict[str, dict[CodeNode, list[CodeNode]] | None ] = {}

    def populate(self, code_nodes: list[CodeNode], dependency_edges: list[DependencyEdge]) -> None:
        self.add_nodes(code_nodes)
        self.add_edges(dependency_edges)
        return

    def get_all_children_by_node_by_graph(self, graph_id: str) -> dict[CodeNode, list[CodeNode]]:
        if self._all_children_by_node_by_graph.get(graph_id, None) is None:
            self._compute_all_children_by_node(graph_id)

        all_children_by_node = self._all_children_by_node_by_graph[graph_id]
        assert all_children_by_node is not None
        return all_children_by_node

    def get_all_parents_by_node_by_graph(self, graph_id: str) -> dict[CodeNode, list[CodeNode]]:
        if self._all_parent_by_node_by_graph.get(graph_id, None) is None:
            self._compute_all_parent_by_node(graph_id)

        all_parents_by_node = self._all_parent_by_node_by_graph[graph_id]
        assert all_parents_by_node is not None
        return all_parents_by_node

    def get_nodes(self, graph_id: str) -> list[CodeNode]:
        return self._graph[self._graph.filter_nodes(lambda node: node.graph_id == graph_id)]

    def get_children_from_node(self, node: CodeNode) -> list[CodeNode]:
        node_index = self._node_indices[node.id]
        return self._graph.find_successors_by_edge(node_index, lambda x: True)

    def get_parent_from_node(self, node: CodeNode, filter_by_relation: DependencyType | None = None) -> list[CodeNode]:
        def filter_function(input: Any) -> bool:
            if filter_by_relation:
                return input == filter_by_relation
            return True

        node_index = self._node_indices[node.id]
        return self._graph.find_predecessors_by_edge(node_index, filter_function)

    def update_node(self, code_node: CodeNode) -> None:
        return

    def add_node(self, node: CodeNode) -> None:
        if node.id in self._node_indices:
            raise IdAlreadyInserted(node.id)

        self._all_children_by_node_by_graph[node.graph_id] = None
        self._all_parent_by_node_by_graph[node.graph_id] = None
        index = self._graph.add_node(node)
        self._node_indices[node.id] = index
        self._node_id_to_graph_id[node.id] = node.graph_id
        self._graph_id_to_node_indices.setdefault(node.graph_id, []).append(index)

    def add_nodes(self, nodes: list[CodeNode]):
        for node in nodes:
            self.add_node(node)

    def add_edge(self, parent_node_id: str, child_node_id: str, weight: Any = None) -> None:
        if parent_node_id not in self._node_indices:
            raise IdNotFound(parent_node_id)

        if child_node_id not in self._node_indices:
            raise IdNotFound(child_node_id)

        if parent_node_id == child_node_id:
            return

        self._all_children_by_node_by_graph[self._node_id_to_graph_id[parent_node_id]] = None
        self._all_parent_by_node_by_graph[self._node_id_to_graph_id[parent_node_id]] = None

        self._all_children_by_node_by_graph[self._node_id_to_graph_id[child_node_id]] = None
        self._all_parent_by_node_by_graph[self._node_id_to_graph_id[child_node_id]] = None

        parent_index = self._node_indices[parent_node_id]
        child_index = self._node_indices[child_node_id]
        self._graph.add_edge(parent_index, child_index, weight)
        return

    def add_edges(self, edges: list[DependencyEdge]):
        for edge in edges:
            self.add_edge(edge.from_node_id, edge.to_node_id, edge.type)

    def _compute_all_children_by_node(self, graph_id: str) -> None:
        self._all_children_by_node_by_graph[graph_id] = {}

        for index in self._graph_id_to_node_indices[graph_id]:
            node = self._graph[index]
            children = self._graph.find_successors_by_edge(index, lambda _: True)
            self._all_children_by_node_by_graph[graph_id][node] = children

        return

    def _compute_all_parent_by_node(self, graph_id: str) -> None:
        self._all_parent_by_node_by_graph[graph_id] = {}

        for index in self._graph_id_to_node_indices[graph_id]:
            node = self._graph[index]
            parent = self._graph.find_predecessors_by_edge(index, lambda _: True)
            self._all_parent_by_node_by_graph[graph_id][node] = parent

        return
