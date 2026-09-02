from backend.domain.entities.llm_message import LLMMessage
from backend.domain.entities.llm_response import LLMResponse
from backend.application.ports.llm_client import LLMClient

class FakeLLMClient(LLMClient):

    def generate(self, messages: list[LLMMessage]) -> LLMResponse:
        pass