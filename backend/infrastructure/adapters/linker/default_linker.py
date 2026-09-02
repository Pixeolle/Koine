from pathlib import Path

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.application.ports.linker import Linker
from backend.domain.entities.dependency_edge import DependencyEdge


class DefaultLinker(Linker):

    def __init__(self):
        pass

    def resolve_dependencies(self, path_to_blocks: dict[Path, list[ParsedBlockDTO]]) -> list[DependencyEdge]:
        return []
