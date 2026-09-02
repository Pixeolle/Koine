import asyncio

from collections.abc import AsyncIterator
from dataclasses import dataclass
from string import Template
from loguru import logger

from backend.domain.agents.agent import Agent, AgentParameters
from backend.domain.enums.output_language import OutputLanguage
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole


@dataclass
class AssistantParameters:
    agent_parameters: AgentParameters
    tracker: LLMUsageTracker
    starting_prompt: str


class Assistant(Agent):

    def __init__(
            self,
            assistant_parameters: AssistantParameters
    ):
        self._starting_prompt = Template(assistant_parameters.starting_prompt)

        super().__init__(tracker=assistant_parameters.tracker, agent_parameter=assistant_parameters.agent_parameters)


    async def respond(self, user_message: str, output_language: OutputLanguage) -> AsyncIterator[str]:
        logger.debug("Start assistant thinking")
        self._agent_context.add_to_context(LLMMessage(
            role=LLMMessageRole.USER,
            content=(
                f"[Respond in {output_language.name.lower()}]\n\n"
                f"{user_message}"
            )
        ))
        await self._call_llm_client()

        while not self._is_task_validated():
            self._agent_context.add_to_context(self._reminder_message(), update_token_count=True)
            await self._call_llm_client()

        response = self._agent_context.context[-1].content
        async for chunk in fake_stream(response):
            yield chunk

        return

    def _is_task_validated(self) -> bool:
        return self._agent_context.context[-1].role is LLMMessageRole.ASSISTANT

    def _reminder_message(self) -> LLMMessage:
        return LLMMessage(
            role=LLMMessageRole.USER,
            content=(
                "You haven't answered the user's question yet - your last turn didn't produce a reply.\n\n"
                "If you're still exploring the graph. that's fine, but don't bose sight of the question: "
                "answer it directly, using what you've found so far. You don't need to explore exhaustively "
                "before answering - a grounded answer based on what you've already checked is better than "
                "continuing to explore in search of certainty you don't need"
            )
        )

    def _build_starting_prompt(self) -> str:
        return self._starting_prompt.substitute()

async def fake_stream(text: str, chuk_size: int = 3):
    words = text.split(" ")
    for index in range(0, len(words), chuk_size):
        yield " ".join(words[index: index + chuk_size]) + " "
        await asyncio.sleep(0.03)