from abc import ABC, abstractmethod

from backend.domain.entities.llm_message import LLMMessage
from backend.domain.entities.llm_response import LLMResponse
from backend.domain.entities.llm_structured_response import LLMStructuredResponse, Template
from backend.domain.entities.llm_tool import LLMTool
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


class LLMClient(ABC):

    @abstractmethod
    async def async_generate(
            self,
            messages: list[LLMMessage],
            tracker: LLMUsageTracker,
            tools: list[LLMTool] | None = None
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def async_generate_structured(
            self,
            messages: list[LLMMessage],
            schema: type[Template],
            tracker: LLMUsageTracker
    ) -> LLMStructuredResponse[Template]:
        pass

    @property
    @abstractmethod
    def call_count(self) -> int:
        pass

    @property
    @abstractmethod
    def input_token_count(self) -> int:
        pass

    @property
    @abstractmethod
    def output_token_count(self) -> int:
        pass

