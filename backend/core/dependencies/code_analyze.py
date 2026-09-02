from pathlib import Path

from backend.application.ports.parser import Parser
from backend.application.ports.linker import Linker
from backend.application.ports.llm_client import LLMClient
from backend.core.settings import settings
from backend.core.dependencies.graph import build_graph_engine
from backend.core.dependencies.llm import build_llm_tokenizer, build_prompt_factory
from backend.domain.services.code_graph_builder import CodeGraphBuilder
from backend.domain.services.code_graph_enricher import CodeGraphEnricher
from backend.domain.enums.supported_language import SupportedLanguage
from backend.infrastructure.adapters.linker.linker_provider import LinkerProvider

def build_parsers() -> dict[SupportedLanguage, Parser]:
    from backend.infrastructure.adapters.parser.parser_provider import ParserProvider
    return {
        language: ParserProvider.from_language(language)
        for language in SupportedLanguage
    }

def build_linkers(project_path: Path, accepted_files: set[Path]) -> dict[SupportedLanguage, Linker]:
    return {
        language: LinkerProvider.from_language_paths(
            language=language,
            project_path=project_path,
            accepted_files=accepted_files
        )
        for language in SupportedLanguage
    }

def build_code_graph_builder() -> CodeGraphBuilder:
    graph_engine = build_graph_engine()
    return CodeGraphBuilder(graph_engine)


def build_code_graph_enricher(llm_client: LLMClient) -> CodeGraphEnricher:
    llm_tokenizer = build_llm_tokenizer()
    prompt_factory = build_prompt_factory()

    return CodeGraphEnricher(
        llm_client,
        llm_tokenizer,
        prompt_factory,
        settings.llm.client.concurrency_limit,
        settings.llm.prompt.min_messages_tokens,
    )

