from pathlib import Path

from backend.application.ports.llm_tokenizer import LLMTokenizer
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from mistral_common.protocol.instruct.messages import (
    AssistantMessage,
    ChatMessageType,
    Roles,
    SystemMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from mistral_common.protocol.instruct.request import ChatCompletionRequest
from mistral_common.protocol.instruct.tool_calls import FunctionCall
from mistral_common.tokens.tokenizers.mistral import MistralTokenizer as SDKMistralTokenizer


class MistralTokenizer(LLMTokenizer):
    def __init__(self, hg_repo: str | None = None, file_path: Path | None = None):

        if hg_repo is None and file_path is None:
            raise ValueError("hg_repo and file_path can't both be None")

        if file_path is not None:
            self._raw_tokenizer = SDKMistralTokenizer.from_file(tokenizer_filename=file_path)
        else:
            assert hg_repo is not None
            self._raw_tokenizer = SDKMistralTokenizer.from_hf_hub(hg_repo)

    def count_token(self, messages: list[LLMMessage] | LLMMessage) -> int:
        if isinstance(messages, LLMMessage):
            messages = [messages]
        chat_completion = _to_chat_completion(messages)

        encoded = self._raw_tokenizer.encode_chat_completion(chat_completion)
        return len(encoded.tokens)

def _to_chat_completion(messages: list[LLMMessage]) -> ChatCompletionRequest[ChatMessageType]:
    sdk_messages: list[ChatMessageType] = [_to_sdk_message(message) for message in messages]

    return ChatCompletionRequest(messages=sdk_messages)

def _to_sdk_message(message: LLMMessage):
    match message.role:
        case LLMMessageRole.SYSTEM:
            return SystemMessage(role=Roles.system, content=message.content)
        case LLMMessageRole.USER:
            return UserMessage(role=Roles.user, content=message.content)
        case LLMMessageRole.ASSISTANT:
            return AssistantMessage(role=Roles.assistant, content=message.content)
        case LLMMessageRole.TOOL_RESULT:
            assert message.tool_calls is not None
            return ToolMessage(
                role=Roles.tool,
                content=message.content,
                tool_call_id=message.tool_calls[0].id
            )
        case LLMMessageRole.TOOL_CALL:
            assert message.tool_calls is not None
            return AssistantMessage(
                role=Roles.assistant,
                tool_calls=[
                    ToolCall(
                        id=tool_call.id,
                        function=FunctionCall(
                            name=tool_call.name,
                            arguments=str(tool_call.arguments)
                        )
                    )
                    for tool_call in message.tool_calls
                ]
            )
