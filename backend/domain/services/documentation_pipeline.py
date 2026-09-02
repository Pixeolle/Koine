from datetime import datetime

from collections.abc import Iterable
from dataclasses import dataclass

from backend.application.ports.document_repository import DocumentRepository
from backend.application.ports.progress_reporter import ProgressEventType, ProgressReporter
from backend.domain.agents.judge import JudgeOrchestrator
from backend.domain.agents.structurer import Structurer
from backend.domain.agents.writer import WriterOrchestrator
from backend.domain.entities.document import DocumentStatus
from backend.domain.entities.documentation import DocumentationCreate, DocumentationStatus, DocumentationUpdate
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


@dataclass
class DocumentationParams:
    documentation_name: str
    fetched_date: datetime
    additional_name: str | None
    filename: str

class DocumentationPipeline:

    def __init__(
            self,
            structurer: Structurer,
            writer_orchestrator: WriterOrchestrator,
            judge_orchestrator: JudgeOrchestrator,
            document_repository: DocumentRepository,
            max_documentation_iteration: int
    ):
        self._structurer = structurer
        self._writer_orchestrator = writer_orchestrator
        self._judge_orchestator = judge_orchestrator

        self._document_repository = document_repository
        self._max_documentation_iteration = max_documentation_iteration

    async def run(
            self,
            documentation_id: str,
            documentation_params: DocumentationParams,
            tracker: LLMUsageTracker,
            progress_reporter: ProgressReporter
    ) -> None:
        self._document_repository.create_documentation(
            DocumentationCreate(
                documentation_id=documentation_id,
                documentation_name=documentation_params.documentation_name,
                fetched_date=documentation_params.fetched_date,
                additional_name=documentation_params.additional_name,
                hash=hash(documentation_params.filename)
            )
        )

        await progress_reporter.report(ProgressEventType.PLANNING_DOCUMENTATION)
        await self._structurer.build(documentation_id)
        await progress_reporter.report(
            ProgressEventType.PLAN_READY,
            documentation_length = self._document_repository.get_documentation_length(documentation_id)
        )

        for iteration in self._documentation_generation(documentation_id):

            await self._writer_orchestrator.run(documentation_id, progress_reporter)
            if iteration != self._max_documentation_iteration:
                await self._judge_orchestator.run(documentation_id, progress_reporter)

        self._document_repository.update_documentation(
            documentation_id,
            DocumentationUpdate(
                status=DocumentationStatus.FINISHED,
                call_used=tracker.total_calls,
                input_token_used=tracker.total_input_tokens,
                output_token_used=tracker.total_output_tokens
            )
        )

        return

    def _documentation_generation(self, graph_id: str) -> Iterable:
        for iteration in range(self._max_documentation_iteration + 1):
            if self._is_documentation_finished(graph_id):
                return
            yield iteration
        return

    def _is_documentation_finished(self, graph_id: str) -> bool:
        draft_documents = list(filter(
            lambda document: document.status is DocumentStatus.DRAFT,
            self._document_repository.get_documents(graph_id)
        ))

        return len(draft_documents) == 0
