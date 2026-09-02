from functools import reduce
from pathlib import Path

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.application.ports.parser import Parser
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.entities.signature_node import SignatureNode
from backend.domain.entities.source_code import SourceCode
from backend.domain.enums.code_block_type import CodeBlockType


class DefaultParser(Parser):

    def parse_source_code(self, source_code: SourceCode) -> tuple[dict[Path, list[ParsedBlockDTO]], list[DependencyEdge]]:
        parsed_block = ParsedBlockDTO(
            id=source_code.path.as_posix(),
            name='file',
            path=source_code.path,
            type=CodeBlockType.MODULE,
            signature=SignatureNode(),
            raw_bytes=source_code.source_code
        )

        return {source_code.path: [parsed_block]}, []

    def parse_source_code_list(
            self,
            source_codes: list[SourceCode]
    ) -> tuple[dict[Path, list[ParsedBlockDTO]], list[DependencyEdge]]:
        return reduce(
            lambda x, y: (x[0] | y[0], x[1] + y[1]),
            [self.parse_source_code(source_code) for source_code in source_codes]
        )
