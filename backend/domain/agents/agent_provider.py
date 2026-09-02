from collections.abc import Callable

from backend.application.ports.document_repository import DocumentRepository
from backend.application.ports.graph_engine import GraphEngine
from backend.domain.agents.agent import AgentParameters
from backend.domain.agents.assisant import Assistant, AssistantParameters
from backend.domain.agents.base_agent_settings import BaseAgentParameters
from backend.domain.agents.judge import Judge, JudgeOrchestrator, JudgeParameters
from backend.domain.agents.structurer import Structurer, StructurerParameters
from backend.domain.agents.tools.tool_factory import ToolFactory
from backend.domain.agents.writer import Writer, WriterOrchestrator, WriterParameters
from backend.domain.entities.document import Document, DocumentStatus
from backend.domain.enums.output_language import OutputLanguage
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


class AgentProvider:

    def __init__(
            self,
            base_parameters: BaseAgentParameters,
            tool_factory: ToolFactory,
            graph_engine: GraphEngine,
            document_repository: DocumentRepository,
            concurrency_limit: int,
            structurer_system_prompt: str,
            structurer_starting_prompt: str,
            writer_system_prompt: str,
            writer_starting_prompt: str,
            writer_starting_block_creation: str,
            writer_starting_block_revision: str,
            judge_system_prompt: str,
            judge_starting_prompt: str,
            assistant_system_prompt: str,
            assistant_starting_prompt: str
    ):
        self._base_parameters = base_parameters
        self._tool_factory = tool_factory
        self._graph_engine = graph_engine
        self._document_repository = document_repository
        self._concurrency_limit = concurrency_limit

        self._structurer_system_prompt = structurer_system_prompt
        self._structurer_starting_prompt = structurer_starting_prompt

        self._writer_system_prompt = writer_system_prompt
        self._writer_starting_prompt = writer_starting_prompt
        self._writer_starting_block_creation = writer_starting_block_creation
        self._writer_starting_block_revision = writer_starting_block_revision

        self._judge_system_prompt = judge_system_prompt
        self._judge_starting_prompt = judge_starting_prompt

        self._assistant_system_prompt = assistant_system_prompt
        self._assistant_starting_prompt = assistant_starting_prompt

    def get_structurer(self, documentation_id: str, output_language: OutputLanguage, tracker: LLMUsageTracker) -> Structurer:
        def documentation_length() -> int:
            return self._document_repository.get_documentation_length(documentation_id)

        agent_parameters = AgentParameters(
            base_parameters=self._base_parameters,
            system_prompt=self._structurer_system_prompt,
            custom_tools=self._tool_factory.build_structurer_tools(documentation_id)
        )

        structurer_parameters = StructurerParameters(
            agent_parameters=agent_parameters,
            tracker=tracker,
            starting_prompt=self._structurer_starting_prompt,
            output_language=output_language,
            count_nodes=self._graph_engine.count_nodes(documentation_id),
            count_root_nodes=self._graph_engine.count_root_nodes(documentation_id),
            documentation_length=documentation_length
        )
        return Structurer(structurer_parameters)

    def get_writer_provider(
            self,
            documentation_id: str,
            output_language: OutputLanguage,
            repository_url: str,
            tracker: LLMUsageTracker
    ) -> Callable[[Document], Writer]:

        def writer_provider(document: Document) -> Writer:
            def document_length() -> int:
                document_entity = self._document_repository.get_document(document.documentation_id, document.document_name)
                return len(document_entity.content)

            agent_parameters = AgentParameters(
                base_parameters=self._base_parameters,
                system_prompt=self._writer_system_prompt,
                custom_tools=self._tool_factory.build_writer_tools(documentation_id, document),
            )

            writer_parameters = WriterParameters(
                agent_parameters=agent_parameters,
                tracker=tracker,
                document=document,
                starting_prompt=self._writer_starting_prompt,
                starting_block_creation=self._writer_starting_block_creation,
                starting_block_revision=self._writer_starting_block_revision,
                output_language=output_language,
                repository_url=repository_url,
                document_length=document_length
            )

            return Writer(writer_parameters)

        return writer_provider

    def get_writer_orchestrator(
            self,
            documentation_id: str,
            output_language: OutputLanguage,
            repository_url: str,
            tracker: LLMUsageTracker
    ) -> WriterOrchestrator:
        return WriterOrchestrator(
            writer_provider=self.get_writer_provider(documentation_id, output_language, repository_url, tracker),
            concurrency_limit=self._concurrency_limit,
            document_repository=self._document_repository
        )

    def get_judge_provider(
            self,
            documentation_id: str,
            output_language: OutputLanguage,
            tracker: LLMUsageTracker
    ) -> Callable[[Document], Judge]:

        def judge_provider(document: Document) -> Judge:
            def is_document_review_empty() -> bool:
                document_entity = self._document_repository.get_document(document.documentation_id, document.document_name)
                return len(document_entity.review) == 0

            def is_document_review_updated() -> bool:
                document_entity = self._document_repository.get_document(document.documentation_id, document.document_name)
                return document_entity.review != document.review

            def is_document_approved() -> bool:
                document_entity = self._document_repository.get_document(document.documentation_id, document.document_name)
                return document_entity.status is DocumentStatus.APPROVED


            agent_parameters = AgentParameters(
                base_parameters=self._base_parameters,
                system_prompt=self._judge_system_prompt,
                custom_tools=self._tool_factory.build_judge_tools(documentation_id, document),
            )

            judge_parameters = JudgeParameters(
                agent_parameters=agent_parameters,
                tracker=tracker,
                document=document,
                starting_prompt=self._judge_starting_prompt,
                output_language=output_language,
                is_document_review_empty=is_document_review_empty,
                is_document_review_updated=is_document_review_updated,
                is_document_approved=is_document_approved
            )

            return Judge(judge_parameters)

        return judge_provider

    def get_judge_orchestrator(
            self,
            documentation_id: str,
            output_language: OutputLanguage,
            tracker: LLMUsageTracker
    ) -> JudgeOrchestrator:
        return JudgeOrchestrator(
            judge_provider=self.get_judge_provider(documentation_id, output_language, tracker),
            concurrency_limit=self._concurrency_limit,
            document_repository=self._document_repository
        )

    def get_assistant(
            self,
            documentation_id: str,
    ) -> Assistant:
        agent_parameters = AgentParameters(
            base_parameters=self._base_parameters,
            system_prompt=self._assistant_system_prompt,
            custom_tools=self._tool_factory.build_assistant_tools(documentation_id),
        )

        tracker = LLMUsageTracker()

        assistant_parameters = AssistantParameters(
            agent_parameters=agent_parameters,
            tracker=tracker,
            starting_prompt=self._assistant_starting_prompt
        )

        return Assistant(assistant_parameters)
