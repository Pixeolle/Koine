import json

from typing import Any

from httpx import AsyncClient
from openai import AsyncOpenAI, omit
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
    ParsedChatCompletion,
)
from openai.types.chat.chat_completion_message_function_tool_call_param import Function
from openai.types.shared_params import FunctionDefinition
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.application.ports.llm_client import LLMClient, Template
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.entities.llm_response import LLMResponse, LLMToolCall
from backend.domain.entities.llm_structured_response import LLMStructuredResponse
from backend.domain.entities.llm_tool import ArgumentType, LLMTool, ToolArgument
from backend.domain.exceptions.empty_response_error import EmptyResponseError
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


class OpenAIClient(LLMClient):
    def __init__(self, model: str, base_url: str, api_key: str, http_client: AsyncClient):
        self.model = model
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client
        )

        self.count_call = 0
        self.count_input_token = 0
        self.count_output_token = 0

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=20),
        stop=stop_after_attempt(5),
        reraise=True
    )
    async def async_generate(self, messages: list[LLMMessage], tracker: LLMUsageTracker, tools: list[LLMTool] | None = None) -> LLMResponse:
        response: ChatCompletion = await self.client.chat.completions.create(
            model=self.model,
            messages=_to_chat_completion_messages(messages),
            tools= omit if tools is None else _to_chat_completion_tools(tools),
        )

        content: str | None = response.choices[0].message.content
        if content is None:
            raise EmptyResponseError(self.model, messages)

        prompt_token_count, completion_token_count = self._update_stats(response, tracker)

        if response.choices[0].message.tool_calls is not None:
            tool_calls = [
                LLMToolCall(id=tool_call.id, name=tool_call.function.name, arguments=json.loads(tool_call.function.arguments))
                for tool_call in response.choices[0].message.tool_calls
            ]
        else:
            tool_calls = None

        return LLMResponse(
            content=str(content),
            prompt_token_count=prompt_token_count,
            completion_token_count=completion_token_count,
            tool_calls=tool_calls
        )

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=20),
        stop=stop_after_attempt(5),
        reraise=True
    )
    async def async_generate_structured(
            self,
            messages: list[LLMMessage],
            schema: type[Template],
            tracker: LLMUsageTracker
    )-> LLMStructuredResponse[Template]:
        response: ParsedChatCompletion = await self.client.chat.completions.parse(
            model=self.model,
            messages=_to_chat_completion_messages(messages),
            response_format=schema
        )

        content: str | None = response.choices[0].message.content
        if content is None:
            raise EmptyResponseError(self.model, messages)

        prompt_token_count, completion_token_count = self._update_stats(response, tracker)

        data = None if response.choices[0].message.refusal else response.choices[0].message.parsed

        return LLMStructuredResponse(
            data=data,
            prompt_token_count=prompt_token_count,
            completion_token_count=completion_token_count
        )

    def _update_stats(
            self,
            response: ChatCompletion | ParsedChatCompletion,
            tracker: LLMUsageTracker
    ) -> tuple[int, int]:
        self.count_call += 1

        assert response.usage is not None
        prompt_token_count = response.usage.prompt_tokens
        self.count_input_token += prompt_token_count
        completion_token_count = response.usage.completion_tokens
        self.count_output_token += completion_token_count

        tracker.record(prompt_token_count, completion_token_count)

        return  prompt_token_count, completion_token_count

    @property
    def call_count(self) -> int:
        return self.count_call

    @property
    def input_token_count(self) -> int:
        return self.count_input_token

    @property
    def output_token_count(self) -> int:
        return self.count_output_token


def _to_chat_completion_messages(messages: list[LLMMessage]) -> list[ChatCompletionMessageParam]:
    return [_to_sdk_message(message) for message in messages]

def _to_sdk_message(message: LLMMessage) -> ChatCompletionMessageParam:
    match message.role:
        case LLMMessageRole.SYSTEM:
            return ChatCompletionSystemMessageParam(role='system', content=message.content)
        case LLMMessageRole.USER:
            return ChatCompletionUserMessageParam(role='user', content=message.content)
        case LLMMessageRole.ASSISTANT:
            return ChatCompletionAssistantMessageParam(role='assistant', content=message.content)
        case LLMMessageRole.TOOL_RESULT:
            assert message.tool_calls is not None
            return ChatCompletionToolMessageParam(
                role='tool',
                content=message.content,
                tool_call_id=message.tool_calls[0].id
            )
        case LLMMessageRole.TOOL_CALL:
            assert message.tool_calls is not None
            return ChatCompletionAssistantMessageParam(role='assistant', tool_calls=[
                ChatCompletionMessageFunctionToolCallParam(
                    type='function',
                    id=tool_call.id,
                    function=Function(
                        name=tool_call.name,
                        arguments=str(tool_call.arguments)
                    )
                )
                for tool_call in message.tool_calls
            ])

def _to_chat_completion_tools(tools: list[LLMTool]) -> list[ChatCompletionFunctionToolParam]:
    return [
        ChatCompletionFunctionToolParam(
            type='function',
            function=FunctionDefinition(
                name=tool.name,
                description=tool.description,
                parameters={
                    'type': 'object',
                    'properties': {
                        arg.name: arg_to_json(arg)
                        for arg in tool.arguments
                    },
                    'required': [arg.name for arg in tool.arguments if arg.required]
                },
                strict=True
            )
        )
        for tool in tools
    ]

def arg_to_json(arg: ToolArgument) -> dict[str, Any]:
    schema: dict[str, Any] = {
        'type': arg.type.value,
        'description': arg.description
    }

    if arg.type is ArgumentType.ARRAY and arg.items is not None:
        schema['items'] = arg_to_json(arg.items)

    if arg.type is ArgumentType.ENUM and arg.enum is not None:
        schema['type'] = 'string'
        schema['enum']= arg.enum

    return schema
