from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from backend.domain.entities.llm_tool_call import LLMToolCall


class LLMMessageRole(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant',
    TOOL_CALL = 'tool_call'
    TOOL_RESULT = 'tool_result'

class LLMMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: LLMMessageRole
    content: str

    tool_calls: list[LLMToolCall] | None = None

    @model_validator(mode='after')
    def check_tool_call_id(self) -> Self:
        if self.role is LLMMessageRole.TOOL_RESULT and self.tool_calls is None:
            raise ValueError("tool_calls can't be null in a tool result message")
        if self.role is LLMMessageRole.TOOL_RESULT and self.tool_calls is not None and len(self.tool_calls) != 1:
            raise ValueError("tool_calls should be one item in a tool result message")
        if self.role is LLMMessageRole.TOOL_CALL and self.tool_calls is None:
            raise ValueError("tool_calls can't be null in a tool call message")
        is_a_tool_message = self.role is not LLMMessageRole.TOOL_RESULT or self.role is not LLMMessageRole.TOOL_CALL
        if self.tool_calls is not None and not is_a_tool_message:
            raise ValueError("tool_call_id can't be defined in a non tool message")
        return self

