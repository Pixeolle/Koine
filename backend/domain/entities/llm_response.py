
from pydantic import BaseModel, ConfigDict

from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.entities.llm_tool_call import LLMToolCall


class LLMResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    tool_calls: list[LLMToolCall] | None

    prompt_token_count: int
    completion_token_count: int

    def to_llm_message(self) -> LLMMessage:
        tool_calls = [
            tool_call.model_copy(deep=True)
            for tool_call in self.tool_calls
        ] if self.tool_calls is not None else None

        is_message_empty = self.tool_calls is None and len(self.content) == 0
        content = self.content if not is_message_empty else "Empty Message"

        return LLMMessage(
            role=LLMMessageRole.ASSISTANT if self.tool_calls is None else LLMMessageRole.TOOL_CALL,
            content=content,
            tool_calls=tool_calls
        )
