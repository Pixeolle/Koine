from abc import ABC, abstractmethod

from backend.domain.entities.llm_message import LLMMessage


class LLMTokenizer(ABC):

    @abstractmethod
    def count_token(self, messages: list[LLMMessage] | LLMMessage) -> int:
        pass
