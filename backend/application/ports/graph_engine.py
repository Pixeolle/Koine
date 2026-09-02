from abc import ABC, abstractmethod

from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.enums.dependency_type import DependencyType


class GraphEngine(ABC):

    @abstractmethod
    def populate(self, code_nodes: list[CodeNode], dependency_edges: list[DependencyEdge]):
        pass

    @abstractmethod
    def get_all_parents_by_node_by_graph(self, graph_id: str) -> dict[CodeNode, list[CodeNode]]:
        pass

    @abstractmethod
    def get_all_children_by_node_by_graph(self, graph_id: str) -> dict[CodeNode, list[CodeNode]]:
        pass

    @abstractmethod
    def get_node(self, graph_id: str, node_id: str) -> CodeNode | None:
        pass

    @abstractmethod
    def get_nodes(self, graph_id: str) -> list[CodeNode]:
        pass

    @abstractmethod
    def get_root_nodes(self, graph_id: str) -> list[CodeNode]:
        pass

    @abstractmethod
    def get_children_from_node_id(self, node_id: str) -> list[CodeNode]:
        pass

    @abstractmethod
    def get_children_from_node(self, node: CodeNode) -> list[CodeNode]:
        pass

    @abstractmethod
    def get_parent_from_node_id(self, node_id: str, filter_by_relation: DependencyType | None = None) -> list[CodeNode]:
        pass

    @abstractmethod
    def get_parent_from_node(self, node: CodeNode, filter_by_relation: DependencyType | None = None) -> list[CodeNode]:
        pass

    @abstractmethod
    def update_node(self, code_node: CodeNode) -> None:
        pass

    @abstractmethod
    def count_root_nodes(self, graph_id: str) -> int:
        pass

    @abstractmethod
    def count_nodes(self, graph_id: str) -> int:
        pass

    @abstractmethod
    def delete_graph(self, graph_id: str) -> None:
        pass
