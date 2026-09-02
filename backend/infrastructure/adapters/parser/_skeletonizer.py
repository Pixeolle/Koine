from collections.abc import Iterable

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.enums.dependency_type import DependencyType


def skeletonize_blocks(parsed_blocks: list[ParsedBlockDTO]
                        ) -> tuple[list[ParsedBlockDTO], list[DependencyEdge]]:
    sorted_parsed_blocks = sorted(parsed_blocks, key=lambda block: (block.start_byte, -block.end_byte) )
    skeletonized_blocks = []
    dependency_edges = []

    for block_index in range(len(sorted_parsed_blocks)):
        block_skeletonizer = _BlockSkeletonizer(sorted_parsed_blocks, block_index)
        skeletonized_block, resolved_dependencies = block_skeletonizer.run()

        skeletonized_blocks.append(skeletonized_block)
        dependency_edges.extend(resolved_dependencies)

    return skeletonized_blocks, dependency_edges


class _BlockSkeletonizer:

    def __init__(self, sorted_parsed_blocks: list[ParsedBlockDTO], index_block: int):
        self.sorted_parsed_blocks = sorted_parsed_blocks
        self.index_block = index_block

        self.target_block = self.sorted_parsed_blocks[self.index_block]

        self.code_skeletonized = b''
        self.skeleton_byte_ranges: list[tuple[int, int]] = []
        self.skeleton_point_range: list[tuple[ tuple[int, int], tuple[int, int] ]] = []

        self.offset = self.target_block.start_byte
        self._max_encountered_byte = self.target_block.start_byte
        self._max_encountered_point = self.target_block.start_point
        self._last_child_end_byte: int | None = None
        self._last_child_end_point: tuple[int, int] | None = None

    def run(self) -> tuple[ParsedBlockDTO, list[DependencyEdge]]:
        resolved_dependencies = []

        for child_block in self._iterate_through_valid_lookaheads():
            resolved_dependencies.append(self._consume_block(child_block))

        if self.has_trailing_bytes:
            self._consume_trailing_bytes()

        if self.is_a_leaf:
            return self.target_block, resolved_dependencies

        return self.target_block.model_copy(update={
            'raw_bytes': self.code_skeletonized,
            'skeleton_byte_ranges': self.skeleton_byte_ranges,
            'skeleton_point_ranges': self.skeleton_point_range
        }), resolved_dependencies

    def _iterate_through_valid_lookaheads(self) -> Iterable[ParsedBlockDTO]:
        def reach_end_of_blocks(futur_index: int):
            return futur_index >= len(self.sorted_parsed_blocks)

        def reach_out_of_target_scope(futur_index: int):
            futur_block = self.sorted_parsed_blocks[futur_index]
            assert futur_block.start_byte is not None
            return self.target_block.end_byte < futur_block.start_byte

        current_index = self.index_block + 1

        while not reach_end_of_blocks(current_index) and not reach_out_of_target_scope(current_index):
            current_block = self.sorted_parsed_blocks[current_index]
            assert current_block.end_byte is not None

            if self._max_encountered_byte < current_block.end_byte:
                yield current_block

            current_index += 1

        return

    def _consume_block(self, block: ParsedBlockDTO) -> DependencyEdge:
        assert self.offset is not None
        assert block.end_byte is not None
        assert self._max_encountered_byte is not None
        assert self._max_encountered_point is not None
        assert block.start_byte is not None
        assert block.start_point is not None

        self._last_child_end_byte = block.end_byte
        self._last_child_end_point = block.end_point

        start = self._max_encountered_byte - self.offset
        end = block.start_byte - self.offset
        self.code_skeletonized += self.target_block.raw_bytes[start: end]

        self.skeleton_byte_ranges.append((self._max_encountered_byte, block.start_byte))
        self.skeleton_point_range.append((self._max_encountered_point, block.start_point))

        if self._max_encountered_byte < block.end_byte:
            self._max_encountered_byte = block.end_byte
            self._max_encountered_point = block.end_point

        self.target_block.signature.children.append(block.signature)

        return DependencyEdge(
            type=DependencyType.STRUCTURAL,
            from_node_id=self.target_block.id,
            to_node_id=block.id
        )

    @property
    def is_a_leaf(self) -> bool:
        return self._last_child_end_byte is None

    @property
    def has_trailing_bytes(self) -> bool:
        if self.is_a_leaf:
            return False

        assert self._last_child_end_byte is not None
        return self._last_child_end_byte < self.target_block.end_byte

    def _consume_trailing_bytes(self):

        assert self._last_child_end_byte is not None
        assert self._last_child_end_point is not None
        assert self.target_block.end_byte is not None
        assert self.target_block.end_point is not None

        start = self._last_child_end_byte - self.offset
        self.code_skeletonized += self.target_block.raw_bytes[start:]

        self.skeleton_byte_ranges.append((self._last_child_end_byte, self.target_block.end_byte))
        self.skeleton_point_range.append((self._last_child_end_point, self.target_block.end_point))
