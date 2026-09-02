from backend.application.ports.llm_client import LLMClient
from backend.application.use_cases.run_documentation_pipeline_use_case import RunDocumentationPipelineUseCase
from backend.core.dependencies.code_analyze import build_linkers, build_parsers
from backend.core.dependencies.generate import build_generate_documentation_use_case
from backend.core.dependencies.ingest import build_ingest_repository_use_case

def build_run_documentation_pipeline_use_case(llm_client: LLMClient) -> RunDocumentationPipelineUseCase:
    return RunDocumentationPipelineUseCase(
        ingest_repository_use_case=build_ingest_repository_use_case(),
        generate_documentation_use_case=build_generate_documentation_use_case(llm_client),
        parsers=build_parsers(),
        linkers_provider=build_linkers
    )
