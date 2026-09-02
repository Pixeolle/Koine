from collections.abc import Callable
from loguru import logger
from pathlib import Path

from backend.application.ports.linker import Linker
from backend.application.ports.parser import Parser
from backend.application.ports.progress_reporter import ProgressEventType, ProgressReporter
from backend.application.use_cases.generate_documentation_use_case import (
    GenerateDocumentationUseCase,
    PipelineParams
)
from backend.application.use_cases.ingest_repository_use_case import IngestRepositoryUseCase
from backend.domain.entities.repository_url import RepositoryURL
from backend.domain.enums.output_language import OutputLanguage
from backend.domain.enums.supported_language import SupportedLanguage
from backend.domain.services.code_graph_builder import BuilderParams
from backend.domain.services.documentation_pipeline import DocumentationParams


class RunDocumentationPipelineUseCase:

    def __init__(
            self,
            ingest_repository_use_case: IngestRepositoryUseCase,
            generate_documentation_use_case: GenerateDocumentationUseCase,
            parsers: dict[SupportedLanguage, Parser],
            linkers_provider: Callable[[Path, set[Path]], dict[SupportedLanguage, Linker]]
    ):
        self._ingest_repository_use_case = ingest_repository_use_case
        self._generate_documentation_use_case = generate_documentation_use_case
        self._parsers = parsers
        self._linkers_provider = linkers_provider

    async def run(
            self,
            end_reporting: Callable[[], None],
            documentation_id: str,
            repository_url: RepositoryURL,
            output_language: OutputLanguage,
            max_documentation_iteration: int,
            progress_reporter: ProgressReporter
    ) -> None:
        try:
            await self._pipeline(
                documentation_id=documentation_id,
                repository_url=repository_url,
                output_language=output_language,
                max_documentation_iteration=max_documentation_iteration,
                progress_reporter=progress_reporter
            )

            await progress_reporter.report(ProgressEventType.COMPLETE)
        except Exception as error:
            logger.exception(error)
            await progress_reporter.report(
                ProgressEventType.ERROR,
                detail=str(error)
            )
        finally:
            end_reporting()

        return

    async def _pipeline(
            self,
            documentation_id: str,
            repository_url: RepositoryURL,
            output_language: OutputLanguage,
            max_documentation_iteration: int,
            progress_reporter: ProgressReporter,
    ) -> None:
        ingested_repository = await self._ingest_repository_use_case.ingest(repository_url, progress_reporter)

        linkers = self._linkers_provider(ingested_repository.project_path, ingested_repository.accepted_files)

        pipeline_params = PipelineParams(
            output_language=output_language,
            repository_url=repository_url.url,
            max_documentation_iteration=max_documentation_iteration
        )

        builder_params = BuilderParams(
            source_codes=ingested_repository.source_codes,
            parsers=self._parsers,
            linkers=linkers
        )

        documentation_params = DocumentationParams(
            documentation_name=ingested_repository.repository_name,
            additional_name=ingested_repository.branch_name,
            fetched_date=ingested_repository.fetched_date,
            filename=ingested_repository.archive_filename
        )

        await self._generate_documentation_use_case.generate(
            documentation_id=documentation_id,
            pipeline_params=pipeline_params,
            builder_params=builder_params,
            documentation_params=documentation_params,
            project_path=ingested_repository.project_path,
            progress_reporter=progress_reporter,
        )

        return
