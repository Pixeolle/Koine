import asyncio

from collections.abc import Callable
from dataclasses import dataclass
from string import Template

from loguru import logger

from backend.application.ports.document_repository import DocumentRepository
from backend.application.ports.progress_reporter import ProgressEventType, ProgressReporter
from backend.domain.agents.agent import Agent, AgentParameters
from backend.domain.entities.document import Document, DocumentStatus
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.enums.output_language import OutputLanguage
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


@dataclass
class JudgeParameters:
    agent_parameters: AgentParameters
    tracker: LLMUsageTracker
    document: Document
    starting_prompt: str
    output_language: OutputLanguage
    is_document_review_updated: Callable[[], bool]
    is_document_review_empty: Callable[[], bool]
    is_document_approved: Callable[[], bool]


class Judge(Agent):

    def __init__(
            self,
            judge_parameters: JudgeParameters
    ):
        self._starting_prompt = Template(judge_parameters.starting_prompt)

        self._output_language = judge_parameters.output_language
        self._document = judge_parameters.document
        self._is_document_review_updated = judge_parameters.is_document_review_updated
        self._is_document_review_empty = judge_parameters.is_document_review_empty
        self._is_document_approved = judge_parameters.is_document_approved

        super().__init__(judge_parameters.tracker, judge_parameters.agent_parameters)

    async def evaluate(self, semaphore: asyncio.Semaphore) -> None:
        logger.debug(f"Start {self._document.document_name} review")
        async with semaphore:
            await self._call_llm_client()

        while not self._is_task_validated():
            self._agent_context.add_to_context(self._reminder_message(), update_token_count=True)
            await self._call_llm_client()

        return

    def _is_task_validated(self) -> bool:
        return (self._is_document_approved()
                or (self._is_document_review_updated() and not self._is_document_review_empty()))

    def _reminder_message(self) -> LLMMessage:
        return LLMMessage(
            role=LLMMessageRole.USER,
            content=(
                "You haven't reached a verdict yet - neither validate_document nor review_document has ben called. "
                "Before this task can be considered done, you must call one of them.\n\n "
                "If you haven't checked anything against the graph yet, start verifying the claims central to "
                "the document's goal.\n\n "
                "If you've already checked enough to have an opinion, don't wait for exhaustive certainty - "
                "call validate_document if what you've verified holds up, or review_document with what you've found "
                "so far if it doesn't."
            )
        )

    def _build_starting_prompt(self) -> str:
        return self._starting_prompt.substitute(
            document_name=self._document.document_name,
            goal=self._document.goal,
            content=self._document.content,
            output_language=self._output_language,
            source_node_ids=self._document.source_node_ids
        )

class JudgeOrchestrator:

    def __init__(
            self,
            judge_provider: Callable[[Document], Judge],
            concurrency_limit: int,
            document_repository: DocumentRepository
    ):
        self._judge_provider = judge_provider
        self._concurrency_limit = concurrency_limit
        self._document_repository = document_repository

    async def run(self, documentation_id: str, progress_reporter: ProgressReporter) -> None:
        draft_documents = list(filter(
            lambda document: document.status is DocumentStatus.DRAFT,
            self._document_repository.get_documents(documentation_id)
        ))

        await progress_reporter.report(
            ProgressEventType.REVIEWING_DOCUMENT,
            total_count=len(draft_documents)
        )

        semaphore = asyncio.Semaphore(self._concurrency_limit)

        judge_workers = [self._judge_provider(document) for document in draft_documents]
        judge_tasks = [asyncio.create_task(worker.evaluate(semaphore)) for worker in judge_workers]

        for completed_tasks, task in enumerate(asyncio.as_completed(judge_tasks), start=1):
            await task
            await progress_reporter.report(
                ProgressEventType.DOCUMENT_REVIEWED,
                completed_count=completed_tasks,
                total_count=len(draft_documents)
            )


        return
