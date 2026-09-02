from backend.application.ports.llm_client import LLMClient
from backend.application.ports.llm_tokenizer import LLMTokenizer
from backend.core.dependencies.document import build_document_repository
from backend.core.dependencies.graph import build_graph_engine
from backend.core.settings import settings
from backend.domain.agents.agent import BaseAgentParameters
from backend.domain.agents.agent_provider import AgentProvider
from backend.domain.agents.tools.tool_factory import ToolFactory
from backend.domain.services.prompt_factory import PromptFactory
from backend.infrastructure.adapters.llm.llm_provider import LLMProvider


def build_llm_client() -> LLMClient:
    return _build_llm_bundle()[0]

def build_llm_tokenizer() -> LLMTokenizer:
    return _build_llm_bundle()[1]

def build_prompt_factory() -> PromptFactory:
    llm_tokenizer = build_llm_tokenizer()
    return PromptFactory.from_prompt_paths(
        output_language=settings.llm.prompt.output_language,
        llm_tokenizer=llm_tokenizer,
        max_context_tokens=settings.llm.client.max_context_tokens,
        system_enrichment_prompt_filepath=settings.llm.prompt.system_enrichment_prompt_filepath,
    )

def build_tool_factory() -> ToolFactory:
    return ToolFactory(
        graph_engine=build_graph_engine(),
        document_repository=build_document_repository()
    )

def build_agent_provider(llm_client: LLMClient) -> AgentProvider:
    compression_system_prompt = settings.agent.compression_system_prompt_filepath.read_text('utf8').strip()

    base_settings = BaseAgentParameters(
        llm_client=llm_client,
        llm_tokenizer=build_llm_tokenizer(),
        max_context_token_length=settings.agent.max_context_token_length,
        max_context_token_length_after_compression=settings.agent.max_context_token_length_after_compression,
        start_percentile_compression=settings.agent.start_percentile_compression,
        end_percentile_compression=settings.agent.end_percentile_compression,
        compression_system_prompt=compression_system_prompt,
    )

    tool_factory = build_tool_factory()

    structurer_system_prompt = settings.agent.structurer.system_prompt_filepath.read_text('utf8').strip()
    structurer_starting_prompt = settings.agent.structurer.starting_prompt_filepath.read_text('utf8').strip()

    writer_system_prompt = settings.agent.writer.system_prompt_filepath.read_text('utf8').strip()
    writer_starting_prompt = settings.agent.writer.starting_prompt_filepath.read_text('utf8').strip()
    writer_starting_block_creation = settings.agent.writer.starting_block_creation_filepath.read_text('utf8').strip()
    writer_starting_block_revision = settings.agent.writer.starting_block_revision_filepath.read_text('utf8').strip()

    judge_system_prompt = settings.agent.judge.system_prompt_filepath.read_text('utf8').strip()
    judge_starting_prompt = settings.agent.judge.starting_prompt_filepath.read_text('utf8').strip()

    assistant_system_prompt = settings.agent.assistant.system_prompt_filepath.read_text('utf8').strip()
    assistant_starting_prompt = settings.agent.assistant.starting_prompt_filepath.read_text('utf8').strip()

    return AgentProvider(
        base_parameters=base_settings,
        tool_factory=tool_factory,
        graph_engine=build_graph_engine(),
        document_repository=build_document_repository(),
        concurrency_limit=settings.llm.client.concurrency_limit,
        structurer_system_prompt=structurer_system_prompt,
        structurer_starting_prompt=structurer_starting_prompt,
        writer_system_prompt=writer_system_prompt,
        writer_starting_prompt=writer_starting_prompt,
        writer_starting_block_creation=writer_starting_block_creation,
        writer_starting_block_revision=writer_starting_block_revision,
        judge_system_prompt=judge_system_prompt,
        judge_starting_prompt=judge_starting_prompt,
        assistant_system_prompt=assistant_system_prompt,
        assistant_starting_prompt=assistant_starting_prompt
    )


def _build_llm_bundle() -> tuple[LLMClient, LLMTokenizer]:
    return LLMProvider.get_llm(settings.llm.client)
