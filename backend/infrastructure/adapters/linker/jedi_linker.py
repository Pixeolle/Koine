from pathlib import Path
from typing import Self

import jedi

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.application.dtos.unresolved_dependency_dto import UnresolvedDependencyDTO
from backend.application.ports.linker import Linker
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.enums.dependency_type import DependencyType


class JediLinker(Linker):

    def __init__(self, jedi_project: jedi.Project, accepted_files: set[Path]):
        self.jedi_project = jedi_project
        self._accepted_files = accepted_files

    @classmethod
    def from_project_path(cls, project_path: Path, accepted_files: set[Path]) -> Self:
        jedi_project = jedi.Project(
            path=project_path,
        )
        return cls(jedi_project=jedi_project, accepted_files=accepted_files)

    def resolve_dependencies(self, path_to_blocks: dict[Path, list[ParsedBlockDTO]]) -> list[DependencyEdge]:
        resolved_dependencies: list[DependencyEdge] = []
        for file_path, file_blocks in path_to_blocks.items():
            absolute_file_path = self.jedi_project.path / file_path.relative_to(file_path.parts[0])
            resolved_dependencies.extend(self._resolve_file(absolute_file_path, file_blocks, path_to_blocks))
        return resolved_dependencies

    def _resolve_file(self,
                      file_path: Path,
                      file_blocks: list[ParsedBlockDTO],
                      path_to_blocks: dict[Path, list[ParsedBlockDTO]]):
        resolved_file_dependencies: list[DependencyEdge]  = []

        jedi_script = jedi.Script(path=file_path, project=self.jedi_project)

        for parsed_block in file_blocks:
            if len(parsed_block.unresolved_dependencies) == 0:
                continue

            resolved_file_dependencies.extend(self._resolve_block(jedi_script, parsed_block, path_to_blocks))

        return resolved_file_dependencies

    def _resolve_block(
            self,
            jedi_script: jedi.Script,
            parsed_block: ParsedBlockDTO,
            path_to_blocks: dict[Path, list[ParsedBlockDTO]]
    ) -> list[DependencyEdge]:
        resolved_block_dependencies: list[DependencyEdge] = []
        for unresolved_dependency in parsed_block.unresolved_dependencies:
            resolved_dependency = self._resolve_dependency(
                unresolved_dependency,
                jedi_script,
                path_to_blocks
            )

            if resolved_dependency is not None:
                resolved_block_dependencies.append(resolved_dependency)

        return resolved_block_dependencies


    def _resolve_dependency(
            self,
            unresolved_dependency: UnresolvedDependencyDTO,
            jedi_script: jedi.Script,
            path_to_blocks: dict[Path, list[ParsedBlockDTO]]
    ) -> DependencyEdge | None:
        line, column = _to_jedi_convention(unresolved_dependency.line, unresolved_dependency.column)

        try:
            reference_names = jedi_script.goto(
                line=line,
                column=column,
                follow_imports=True,
                follow_builtin_imports=False,
            )
        except Exception as _:
            self.jedi_project = jedi.Project(path=self.jedi_project.path)
            return None

        if len(reference_names) == 0:
            return None

        reference_name = reference_names[0]

        if reference_name.module_path not in self._accepted_files:
            return None

        try:
            relative_path = reference_name.module_path.relative_to(self.jedi_project.path.parent)
        except Exception:
            return None
        skeletonized_blocks = path_to_blocks.get(relative_path)

        if skeletonized_blocks is None:
            return None

        start = reference_name.get_definition_start_position()
        end = reference_name.get_definition_end_position()
        absolute_start = _from_jedi_convention(start[0], start[1])
        absolute_end = _from_jedi_convention(end[0], end[1])
        source_block = _find_parent_block(absolute_start, absolute_end, skeletonized_blocks)

        if source_block is None:
            return None

        return DependencyEdge(
            type=DependencyType.CALL,
            from_node_id=unresolved_dependency.parsed_block_id,
            to_node_id=source_block.id
        )

def _to_jedi_convention(line: int, column: int):
    return line + 1, column

def _from_jedi_convention(line: int, column: int):
    return line - 1 if line is not None else 0, column if column is not None else 0

def _find_parent_block(
        start_point: tuple[int, int],
        end_point: tuple[int, int],
        skeletonized_blocks: list[ParsedBlockDTO]
) -> ParsedBlockDTO | None:
    for skeletonized_block in skeletonized_blocks:
        assert skeletonized_block.skeleton_point_ranges is not None
        for point_range in skeletonized_block.skeleton_point_ranges:
            is_start_between = _is_point_between(start_point, point_range[0], point_range[1])
            is_end_between = _is_point_between(end_point, point_range[0], point_range[1])
            is_inside = is_start_between and is_end_between
            is_the_block = start_point == skeletonized_block.start_point and end_point == skeletonized_block.end_point
            if is_inside or is_the_block:
                return skeletonized_block

    return None

def _is_point_between(point: tuple[int, int], start: tuple[int, int], end: tuple[int, int]) -> bool:
    return _is_point_after(point, start) and _is_point_before(point, end)

def _is_point_after(point: tuple[int, int], reference: tuple[int, int]) -> bool:
    is_on_next_lines = point[0] > reference[0]
    is_on_same_line = point[0] == reference[0]
    is_on_next_columns = point[1] > reference[1]
    is_on_same_column = point[1] == reference[1]

    return is_on_next_lines or (is_on_same_line and (is_on_same_column or is_on_next_columns))

def _is_point_before(point: tuple[int, int], reference: tuple[int, int]) -> bool:
    is_on_previous_lines = point[0] < reference[0]
    is_on_same_line = point[0] == reference[0]
    is_on_previous_columns = point[1] < reference[1]
    is_on_same_column = point[1] == reference[1]

    return is_on_previous_lines or (is_on_same_line and (is_on_same_column or is_on_previous_columns))
