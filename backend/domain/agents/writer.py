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
class WriterParameters:
    agent_parameters: AgentParameters
    tracker: LLMUsageTracker
    document: Document
    starting_prompt: str
    starting_block_creation: str
    starting_block_revision: str
    output_language: OutputLanguage
    repository_url: str
    document_length: Callable[[], int]


class Writer(Agent):

    def __init__(
            self,
            writer_parameters: WriterParameters
    ):
        self._starting_prompt = Template(writer_parameters.starting_prompt)
        self._starting_prompt_creation = Template(writer_parameters.starting_block_creation)
        self._starting_prompt_revision = Template(writer_parameters.starting_block_revision)

        self._output_language = writer_parameters.output_language
        self._repository_url = writer_parameters.repository_url
        self._document = writer_parameters.document
        self._document_length = writer_parameters.document_length

        super().__init__(writer_parameters.tracker, writer_parameters.agent_parameters)

    async def run(self, semaphore: asyncio.Semaphore) -> None:
        logger.debug(f"Start {self._document.document_name} documentation")
        async with semaphore:
            await self._call_llm_client()

            while not self._is_task_validated():
                self._agent_context.add_to_context(self._reminder_message(), update_token_count=True)
                await self._call_llm_client()

        return

    def _is_task_validated(self) -> bool:
        return self._document_length() > 0

    def _reminder_message(self) -> LLMMessage:
        return LLMMessage(
            role=LLMMessageRole.USER,
            content=(
                "No content has been saved for this document yet - update@document hasn't been called. Before this "
                "task can be considered done, you must call it at least once.\n\n "
                "If you haven't explored anything yet, start with get_root_nodes.\n\n "
                "If you've already explored but haven't written anything, don't wait for a perfect first draft - save "
                "what you have now, even if incomplete. update_document is a checkpoint, not a final commit; "
                "you can call it again to refine once something exists to build on."
            )
        )

    def _build_starting_prompt(self) -> str:
        is_revision = len(self._document.review) > 0

        if is_revision:
            state_block = self._starting_prompt_revision.substitute(
                review=self._document.review,
                content=self._document.content,
                source_node_ids=self._document.source_node_ids
            )
        else:
            state_block = self._starting_prompt_creation.substitute()

        return self._starting_prompt.substitute(
            repository_url=self._repository_url,
            output_language=self._output_language.text,
            document_name=self._document.document_name,
            document_goal=self._document.goal,
            state_block=state_block
        )

class WriterOrchestrator:

    def __init__(
            self,
            writer_provider: Callable[[Document], Writer],
            concurrency_limit: int,
            document_repository: DocumentRepository
    ):
        self._writer_provider = writer_provider
        self._concurrency_limit = concurrency_limit
        self._document_repository = document_repository

    async def run(self, documentation_id: str, progress_reporter: ProgressReporter) -> None:
        draft_documents = list(filter(
            lambda document: document.status is DocumentStatus.DRAFT,
            self._document_repository.get_documents(documentation_id)
        ))

        await progress_reporter.report(
            ProgressEventType.WRITING_DOCUMENT,
            total_count=len(draft_documents)
        )

        semaphore = asyncio.Semaphore(self._concurrency_limit)

        writer_workers = [self._writer_provider(document) for document in draft_documents]
        writer_tasks = [asyncio.create_task(worker.run(semaphore)) for worker in writer_workers]

        for completed_tasks, task in enumerate(asyncio.as_completed(writer_tasks), start=1):
            await task
            await progress_reporter.report(
                ProgressEventType.DOCUMENT_WRITTEN,
                completed_count=completed_tasks,
                total_count=len(draft_documents)
            )

        return
