from abc import ABC, abstractmethod
from pathlib import Path

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.domain.entities.dependency_edge import DependencyEdge


class Linker(ABC):

    @abstractmethod
    def resolve_dependencies(self, path_to_blocks: dict[Path, list[ParsedBlockDTO]]) -> list[DependencyEdge]:
        pass
