import asyncio

from pathlib import Path
from dataclasses import dataclass

from loguru import logger

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.application.mappers.create_code_node import CreateCodeNode
from backend.application.ports.graph_engine import GraphEngine
from backend.application.ports.linker import Linker
from backend.application.ports.parser import Parser
from backend.application.ports.progress_reporter import ProgressEventType, ProgressReporter
from backend.domain.entities.dependency_edge import DependencyEdge
from backend.domain.entities.source_code import SourceCode
from backend.domain.enums.supported_language import SupportedLanguage


@dataclass
class BuilderParams:
    source_codes: list[SourceCode]
    parsers: dict[SupportedLanguage, Parser]
    linkers: dict[SupportedLanguage, Linker]


class CodeGraphBuilder:

    def __init__(self, graph_engine: GraphEngine):
        self._graph_engine = graph_engine

    async def build(
            self,
            graph_id: str,
            builder_params: BuilderParams,
            progress_reporter: ProgressReporter
    ) -> None:
        logger.info('Start Graph construction')
        await progress_reporter.report(ProgressEventType.BUILDING_CODE_GRAPH)

        filtered_source_codes = _filter_source_codes(builder_params.source_codes)

        await progress_reporter.report(ProgressEventType.PARSING_SOURCE_CODE)
        try:
            language_to_path_to_parsed_blocks, dependency_edges = await asyncio.to_thread(
                self._parse_source_codes,
                filtered_source_codes=filtered_source_codes,
                parsers=builder_params.parsers,
            )
        except Exception as error:
            raise
        await progress_reporter.report(
            ProgressEventType.SOURCE_CODE_PARSED,
            structural_dependencies=len(dependency_edges)
        )


        await progress_reporter.report(ProgressEventType.LINKING_DEPENDENCIES)
        try:
            dependency_linked = await asyncio.to_thread(
                self._resolve_dependencies,
                language_to_path_to_parsed_blocks=language_to_path_to_parsed_blocks,
                linkers=builder_params.linkers,
            )
        except Exception as error:
            raise
        await progress_reporter.report(
            ProgressEventType.DEPENDENCIES_LINKED,
            dependency_linked=len(dependency_linked)
        )

        dependency_edges.extend(dependency_linked)

        code_nodes = [
            CreateCodeNode.from_parsed_code_block(graph_id, parsed_block_dto)
            for path_to_parsed_blocks in language_to_path_to_parsed_blocks.values()
            for parsed_blocks in path_to_parsed_blocks.values()
            for parsed_block_dto in parsed_blocks
        ]

        self._graph_engine.populate(code_nodes=code_nodes, dependency_edges=dependency_edges)
        await progress_reporter.report(
            ProgressEventType.CODE_GRAPH_BUILT,
            nodes=len(code_nodes),
            dependencies=len(dependency_edges)
        )

        return

    def _parse_source_codes(
            self,
            filtered_source_codes: dict[SupportedLanguage, list[SourceCode]],
            parsers: dict[SupportedLanguage, Parser],
    ) -> tuple[dict[SupportedLanguage, dict[Path, list[ParsedBlockDTO]] ], list[DependencyEdge]]:

        language_to_path_to_parsed_blocks: dict[SupportedLanguage, dict[Path, list[ParsedBlockDTO]] ] = {}
        dependency_edges: list[DependencyEdge] = []

        for language, source_codes in filtered_source_codes.items():
            path_to_parsed_blocks_extracted, dependency_edges_extracted = parsers[language].parse_source_code_list(source_codes)

            language_to_path_to_parsed_blocks[language] = path_to_parsed_blocks_extracted
            dependency_edges.extend(dependency_edges_extracted)

        logger.info(
            "{number_of_blocks} Blocks found - {number_of_dependency} Structural Dependency found",
            number_of_blocks=sum([
                len(parsed_blocks)
                for path_to_parsed_blocks in language_to_path_to_parsed_blocks.values()
                for parsed_blocks in path_to_parsed_blocks.values()
            ]),
            number_of_dependency=len(dependency_edges)
        )

        return language_to_path_to_parsed_blocks, dependency_edges

    def _resolve_dependencies(
            self,
            language_to_path_to_parsed_blocks: dict[SupportedLanguage, dict[Path, list[ParsedBlockDTO]] ],
            linkers: dict[SupportedLanguage, Linker]
    ) -> list[DependencyEdge]:
        dependency_edges: list[DependencyEdge] = []

        for language, path_to_parsed_blocks in language_to_path_to_parsed_blocks.items():
            dependency_edges.extend(linkers[language].resolve_dependencies(path_to_parsed_blocks))

        logger.info(f"{len(dependency_edges)} Dependency resolved by the Linker")

        return dependency_edges

def _filter_source_codes(source_codes: list[SourceCode]) -> dict[SupportedLanguage, list[SourceCode]]:
    filtered_source_codes = {}
    for source_code in source_codes:
        language = _find_language(source_code)

        if language is None:
            continue

        filtered_source_codes.setdefault(language, []).append(source_code)

    return filtered_source_codes

def _find_language(source_code: SourceCode) -> SupportedLanguage | None :
    for supported_language in SupportedLanguage:
        if source_code.get_extension in supported_language.extensions:
            return supported_language

    return SupportedLanguage.DEFAULT
