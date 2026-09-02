from pydantic import BaseModel

from backend.domain.enums.dependency_type import DependencyType


class DependencyEdge(BaseModel):
    type: DependencyType
    from_node_id: str
    to_node_id: str
