from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from backend.application.dtos.unresolved_dependency_dto import UnresolvedDependencyDTO
from backend.domain.entities.signature_node import SignatureNode
from backend.domain.enums.code_block_type import CodeBlockType


class ParsedBlockDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    path: Path
    parent: ParsedBlockDTO | None = None
    type: CodeBlockType
    signature: SignatureNode
    raw_bytes: bytes
    skeleton_byte_ranges: list[tuple[int, int]] | None = None
    start_byte: int | None = None
    end_byte: int | None = None
    skeleton_point_ranges: list[tuple[tuple[int, int], tuple[int, int]]] | None = None
    start_point: tuple[int, int] | None = None
    end_point: tuple[int, int] | None = None
    unresolved_dependencies: tuple[UnresolvedDependencyDTO] = ()

    @property
    def local_fqn(self) -> str | None:
        if self.type is CodeBlockType.MODULE:
            return None

        if self.parent is None:
            return self.name

        parent_local_fqn = self.parent.local_fqn
        if parent_local_fqn is None:
            return self.name

        return f'{self.parent.local_fqn}.{self.name}'
