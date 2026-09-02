import re

from functools import reduce
from pathlib import Path

import tree_sitter
import tree_sitter_python as tspython

from tree_sitter import Language, Node

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.application.dtos.unresolved_dependency_dto import UnresolvedDependencyDTO
from backend.application.ports.parser import Parser
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.entities.signature_node import SignatureNode
from backend.domain.entities.source_code import SourceCode
from backend.domain.enums.code_block_type import CodeBlockType
from backend.domain.enums.supported_language import SupportedLanguage
from backend.domain.exceptions.orphan_code import OrphanCode
from backend.infrastructure.adapters.parser._skeletonizer import skeletonize_blocks


class TreeSitterParser(Parser):

    def __init__(self, language: SupportedLanguage):
        _GRAMMAR_MAP = {
            SupportedLanguage.PYTHON: tspython.language()
        }

        self.language = Language(_GRAMMAR_MAP[language])
        self.parser = tree_sitter.Parser(self.language)

    def parse_source_code(
            self,
            source_code: SourceCode
    ) -> tuple[dict[Path, list[ParsedBlockDTO]], list[DependencyEdge]]:
        parsed_tree = self.parser.parse(source_code.source_code)
        root_node = parsed_tree.root_node

        parsed_blocks: list[ParsedBlockDTO] = []
        for code_block_type in CodeBlockType:
            parsed_blocks += self._extract_parsed_blocks(
                code_block_type,
                root_node,
                source_code.path,
                default_name='module' if code_block_type is CodeBlockType.MODULE else 'default_name'
            )

        skeletonized_parsed_blocks, dependency_edges = skeletonize_blocks(parsed_blocks)
        filtered_parsed_blocks, filtered_dependency_edges = _filter_empty_module(
            skeletonized_parsed_blocks,
            dependency_edges
        )
        blocks_with_unresolved_dependencies = self._extract_external_dependencies(
            root_node,
            filtered_parsed_blocks
        )
        blocks_with_parent = _resolve_parent(blocks_with_unresolved_dependencies, filtered_dependency_edges)

        return {source_code.path : blocks_with_parent}, filtered_dependency_edges

    def parse_source_code_list(
            self,
            source_codes: list[SourceCode]
    ) -> tuple[dict[Path, list[ParsedBlockDTO]], list[DependencyEdge]]:
        return reduce(
            lambda x, y: (x[0] | y[0], x[1] + y[1]),
            [self.parse_source_code(source_code) for source_code in source_codes]
        )

    def _extract_parsed_blocks(
            self,
            code_block_type: CodeBlockType,
            root_node: Node,
            filepath: Path,
            default_name: str = 'default_name'
    ) -> list[ParsedBlockDTO]:
        _REQUEST_MAP = {
            CodeBlockType.MODULE: '(module) @code',
            CodeBlockType.CLASS: '(class_definition (identifier) @name body: (block) @body) @code',
            CodeBlockType.FUNCTION: '(function_definition (identifier) @name body: (block) @body) @code'
        }

        block_query = _REQUEST_MAP[code_block_type]
        raw_blocks: list[dict[str, Node]] = self._extract_captures(root_node, block_query)

        parsed_blocks: list[ParsedBlockDTO] = []
        for raw_block in raw_blocks:
            parsed_blocks.append(_extract_parsed_block(
                root_node=root_node,
                raw_block=raw_block,
                code_block_type=code_block_type,
                filepath=filepath,
                default_name=default_name
            ))

        return parsed_blocks

    def _extract_captures(self, root_node: Node, s_expression_query: str) -> list[dict[str, Node]]:
        query = tree_sitter.Query(self.language, s_expression_query)
        query_cursor = tree_sitter.QueryCursor(query)

        query_results = query_cursor.matches(root_node)

        return _format_result(query_results)

    def _extract_external_dependencies(
            self,
            root_node: Node,
            blocks: list[ParsedBlockDTO]
    ) -> list[ParsedBlockDTO]:
        UNRESOLVED_DEPENDENCIES_QUERY = """
        [
            (call
                function: [
                    (attribute
                        attribute: (identifier) @dependency
                    )
                    (identifier) @dependency
                    ]
            )
            (class_definition
                superclasses: (argument_list (identifier) @dependency))
            (import_from_statement
                name: ((dotted_name (identifier) @dependency)))
        ]
        """
        dependencies = self._extract_captures(root_node, UNRESOLVED_DEPENDENCIES_QUERY)
        dependencies += self._extract_type_dependencies(root_node)
        if len(dependencies) == 0:
            return blocks.copy()

        id_to_dependencies: dict[str, list[UnresolvedDependencyDTO]] = {
            block.id: [] for block in blocks
        }

        for dependency in dependencies:
            node = dependency['dependency']
            parent_block = _find_parent_block(node, blocks)

            id_to_dependencies[parent_block.id].append(UnresolvedDependencyDTO(
                parsed_block_id=parent_block.id,
                line=node.start_point.row,
                column=node.start_point.column,
                start_byte=node.start_byte,
                end_byte=node.end_byte
            ))

        blocks_with_dependencies = []
        for block in blocks:
            blocks_with_dependencies.append(block.model_copy(
                update={'unresolved_dependencies': tuple(id_to_dependencies[block.id])}
            ))

        return blocks_with_dependencies

    def _extract_type_dependencies(self, root_node: Node) -> list[dict[str, Node]]:
        TYPE_TAG_QUERY = """(type) @type"""
        TYPE_DEPENDENCIES_QUERY = """(identifier) @dependency"""

        dependencies: list[dict[str, Node]] = []

        types_tag = self._extract_captures(root_node, TYPE_TAG_QUERY)

        for type_tag in types_tag:
            node = type_tag['type']
            dependencies += self._extract_captures(node, TYPE_DEPENDENCIES_QUERY)

        return dependencies


def _resolve_parent(blocks: list[ParsedBlockDTO], dependency_edges: list[DependencyEdge]) -> list[ParsedBlockDTO]:
    id_to_parent: dict[str, ParsedBlockDTO | None] = {
        block.id: None for block in blocks
    }

    for dependency_edge in dependency_edges:
        id_to_parent[dependency_edge.to_node_id] = _find_block_by_id(
            id=dependency_edge.from_node_id,
            blocks=blocks
        )

    blocks_with_parent = []
    for block in blocks:
        blocks_with_parent.append(block.model_copy(
            update={'parent': id_to_parent[block.id]}
        ))

    return blocks_with_parent

def _format_result(query_results: list[tuple[int, dict[str, list[Node]]]]) -> list[dict[str, Node]]:
    formated_result = []
    for element in query_results:
        body = element[1]
        extracted_dictionary = {key: node_list[0] for key, node_list in body.items()}

        formated_result.append(extracted_dictionary)

    return formated_result

def _find_parent_block(node: Node, skeletonized_blocks: list[ParsedBlockDTO]) -> ParsedBlockDTO:
    for skeletonized_block in skeletonized_blocks:
        assert skeletonized_block.skeleton_byte_ranges is not None
        for segment in skeletonized_block.skeleton_byte_ranges:
            if node.start_byte >= segment[0] and node.end_byte <= segment[1]:
                return skeletonized_block

    raise OrphanCode(node)

def _find_block_by_id(id: str, blocks: list[ParsedBlockDTO]) -> ParsedBlockDTO | None:
    for block in blocks:
        if block.id == id:
            return block

    return None

def _extract_signature(root_node: Node, node: Node, body: Node) -> SignatureNode:
    start = node.start_byte
    end = body.start_byte - 1
    signature_byte = root_node.text[start: end]
    signature_str = str(signature_byte.decode('utf8')).strip()
    return SignatureNode(signature=signature_str)

def _extract_parsed_block(
        root_node: Node,
        raw_block: dict[str, Node],
        code_block_type: CodeBlockType,
        filepath: Path,
        default_name: str
) -> ParsedBlockDTO:
    code = raw_block['code']

    code_byte = code.text
    assert code_byte is not None

    parsed_block_id = (f'{filepath.as_posix()}_'
                       f'{code.start_point.row}:{code.start_point.column}_'
                       f'{code.end_point.row}:{code.end_point.column}')

    if code_block_type is not code_block_type.MODULE:
        body = raw_block['body']
        signature_node = _extract_signature(root_node, code, body)

        node_name = raw_block['name']
        name = str(node_name.text.decode('utf8'))

    else:
        signature_node = SignatureNode()
        name = default_name

    start_point = (code.start_point.row, code.start_point.column)
    end_point = (code.end_point.row, code.end_point.column)

    return ParsedBlockDTO(
        id=parsed_block_id,
        name=name,
        path=filepath,
        type=code_block_type,
        signature=signature_node,
        raw_bytes=code_byte,
        skeleton_byte_ranges=[(code.start_byte, code.end_byte)],
        start_byte=code.start_byte,
        end_byte=code.end_byte,
        skeleton_point_ranges=[(start_point, end_point)],
        start_point=start_point,
        end_point=end_point
    )

def _filter_empty_module(
        blocks: list[ParsedBlockDTO],
        dependencies: list[DependencyEdge]
) -> tuple[list[ParsedBlockDTO], list[DependencyEdge]]:
    def get_module(blocks : list[ParsedBlockDTO]) -> ParsedBlockDTO | None:
        for block in blocks:
            if block.type is CodeBlockType.MODULE:
                return block
        return None

    def content_str(raw_bytes: bytes) -> str:
        raw_str = str(raw_bytes.decode('utf8'))
        return re.sub(r'\s+', '', raw_str)

    module = get_module(blocks)

    if module is None:
        return blocks, dependencies

    is_module_empty = len(content_str(module.raw_bytes)) == 0
    if not is_module_empty:
        return blocks, dependencies

    filtered_dependencies = list(filter(
        lambda dependency: dependency.from_node_id != module.id and dependency.to_node_id != module.id,
        dependencies
    ))

    filtered_blocks = list(filter(
        lambda block: block.type is not CodeBlockType.MODULE,
        blocks
    ))

    return filtered_blocks, filtered_dependencies
