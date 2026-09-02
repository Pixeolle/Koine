from abc import ABC, abstractmethod
from pathlib import Path

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.entities.source_code import SourceCode


class Parser(ABC):

    @abstractmethod
    def parse_source_code(self, source_code: SourceCode) -> tuple[dict[Path, list[ParsedBlockDTO]], list[DependencyEdge]]:
        pass

    @abstractmethod
    def parse_source_code_list(self, source_codes: list[SourceCode]) -> tuple[dict[Path, list[ParsedBlockDTO]], list[DependencyEdge]]:
        pass
