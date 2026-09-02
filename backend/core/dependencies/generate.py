from backend.application.ports.llm_client import LLMClient
from backend.application.use_cases.generate_documentation_use_case import GenerateDocumentationUseCase
from backend.core.dependencies.code_analyze import build_code_graph_builder, build_code_graph_enricher
from backend.core.dependencies.graph import build_graph_engine
from backend.core.dependencies.document import build_document_repository
from backend.core.dependencies.llm import build_agent_provider


def build_generate_documentation_use_case(llm_client: LLMClient) -> GenerateDocumentationUseCase:
    graph_engine = build_graph_engine()
    document_repository = build_document_repository()

    code_graph_builder = build_code_graph_builder()
    code_graph_enricher = build_code_graph_enricher(llm_client)
    agent_provider = build_agent_provider(llm_client)

    return GenerateDocumentationUseCase(
        graph_engine=graph_engine,
        document_repository=document_repository,
        code_graph_builder=code_graph_builder,
        code_graph_enricher=code_graph_enricher,
        agent_provider=agent_provider
    )


