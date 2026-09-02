from collections.abc import Callable
from dataclasses import dataclass
from string import Template

from loguru import logger

from backend.domain.agents.agent import Agent, AgentParameters
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.enums.output_language import OutputLanguage
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


@dataclass
class StructurerParameters:
    agent_parameters: AgentParameters
    tracker: LLMUsageTracker
    starting_prompt: str
    output_language: OutputLanguage
    count_nodes: int
    count_root_nodes: int
    documentation_length: Callable[[], int]


class Structurer(Agent):

    def __init__(
            self,
            structurer_parameters: StructurerParameters
    ):
        self._starting_prompt = Template(structurer_parameters.starting_prompt)
        self._output_language = structurer_parameters.output_language
        self._count_nodes = structurer_parameters.count_nodes
        self._count_root_nodes = structurer_parameters.count_root_nodes
        self._documentation_length = structurer_parameters.documentation_length

        super().__init__(structurer_parameters.tracker, structurer_parameters.agent_parameters)


    async def build(self, graph_id: str) -> None:
        logger.debug(f"Start {graph_id} documentation structure")
        await self._call_llm_client()

        while not self._is_task_validated():
            self._agent_context.add_to_context(self._reminder_message(), update_token_count=True)
            await self._call_llm_client()

        return

    def _is_task_validated(self) -> bool:
        return self._documentation_length() > 0

    def _reminder_message(self) -> LLMMessage:
        return LLMMessage(
            role=LLMMessageRole.USER,
            content=(
                "You haven't registered any document yet - get_documents currently returns nothing for this codebase. "
                "Before this task can be considered done, you must call create_documenta at least once.\n\n "
                "If you haven't explored the graph yet, start with get_root_nodes.\n\n"
                "If you've already explored but haven't committed to a plan, that hesitation isn't useful here - "
                "register what you've found so far, even if it isn't perfect. You can still create additional document "
                "or delete_document a wrong entry afterward; nothing here is final."
            )
        )

    def _build_starting_prompt(self) -> str:
        return self._starting_prompt.substitute(
            root_node_count=self._count_root_nodes,
            total_node_count=self._count_nodes,
            output_language=self._output_language.text
        )
