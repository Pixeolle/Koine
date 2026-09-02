import shutil
from dataclasses import dataclass

from loguru import logger
from contextlib import AsyncExitStack
from pathlib import Path

from backend.application.ports.progress_reporter import ProgressReporter
from backend.application.ports.document_repository import DocumentRepository
from backend.application.ports.graph_engine import GraphEngine
from backend.domain.agents.agent_provider import AgentProvider
from backend.domain.enums.output_language import OutputLanguage
from backend.domain.services.code_graph_builder import BuilderParams, CodeGraphBuilder
from backend.domain.services.code_graph_enricher import CodeGraphEnricher
from backend.domain.services.documentation_pipeline import DocumentationParams, DocumentationPipeline
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


@dataclass
class PipelineParams:
    output_language: OutputLanguage
    repository_url: str
    max_documentation_iteration: int


class GenerateDocumentationUseCase:
    def __init__(
            self,
            graph_engine: GraphEngine,
            document_repository: DocumentRepository,
            code_graph_builder: CodeGraphBuilder,
            code_graph_enricher: CodeGraphEnricher,
            agent_provider: AgentProvider,
    ):
        self._graph_engine = graph_engine
        self._document_repository = document_repository
        self._code_graph_builder = code_graph_builder
        self._code_graph_enricher = code_graph_enricher
        self._agent_provider = agent_provider
        self._documentation_pipeline: DocumentationPipeline | None = None

    async def generate(
            self,
            documentation_id: str,
            pipeline_params: PipelineParams,
            builder_params: BuilderParams,
            documentation_params: DocumentationParams,
            project_path: Path,
            progress_reporter: ProgressReporter,
    ) -> None:
        tracker = LLMUsageTracker()

        async with AsyncExitStack() as stack:
            stack.callback(self._finish_documentation, project_path)

            self._documentation_pipeline = self._build_documentation_pipeline(
                documentation_id,
                pipeline_params,
                tracker
            )

            await self._code_graph_builder.build(
                graph_id=documentation_id,
                builder_params=builder_params,
                progress_reporter=progress_reporter
            )

            await self._code_graph_enricher.run(
                self._graph_engine,
                documentation_id,
                tracker,
                progress_reporter
            )

            assert self._documentation_pipeline is not None
            await self._documentation_pipeline.run(
                documentation_id,
                documentation_params,
                tracker,
                progress_reporter
            )

        return

    def _build_documentation_pipeline(
            self,
            documentation_id: str,
            pipeline_params: PipelineParams,
            tracker: LLMUsageTracker
    ) -> DocumentationPipeline:
        return DocumentationPipeline(
            structurer=self._agent_provider.get_structurer(
                documentation_id,
                pipeline_params.output_language,
                tracker
            ),
            writer_orchestrator=self._agent_provider.get_writer_orchestrator(
                documentation_id,
                pipeline_params.output_language,
                pipeline_params.repository_url,
                tracker
            ),
            judge_orchestrator=self._agent_provider.get_judge_orchestrator(
                documentation_id,
                pipeline_params.output_language,
                tracker
            ),
            document_repository=self._document_repository,
            max_documentation_iteration=pipeline_params.max_documentation_iteration
        )

    def _finish_documentation(self, project_path: Path) -> None:
        logger.info(f"Documentation Finished")
        shutil.rmtree(project_path)

        return