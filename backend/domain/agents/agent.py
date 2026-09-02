import inspect
import json

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from loguru import logger

from backend.domain.agents.agent_context import AgentContext
from backend.domain.agents.base_agent_settings import BaseAgentParameters
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.entities.llm_response import LLMResponse
from backend.domain.entities.llm_tool import ArgumentType, LLMTool, ToolArgument
from backend.domain.entities.llm_tool_call import LLMToolCall
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


@dataclass
class AgentParameters:
    base_parameters: BaseAgentParameters
    system_prompt: str
    custom_tools: list[LLMTool] | None = None

class Agent(ABC):

    def __init__(
            self,
            tracker: LLMUsageTracker,
            agent_parameter: AgentParameters
    ):
        self._llm_client = agent_parameter.base_parameters.llm_client
        self._tracker = tracker
        self._tools: dict[str, LLMTool] = self._init_tools(agent_parameter.custom_tools)
        self._agent_context = AgentContext(
            agent_parameter.system_prompt,
            self._build_starting_prompt,
            self._tools,
            tracker,
            agent_parameter.base_parameters
        )


    def reset(self, custom_tools: list[LLMTool] | None = None) -> None:
        self._tools = self._init_tools(custom_tools)
        self._agent_context.reset()

    def new_task(self) -> None:
        self._agent_context.new_task()

    def _init_tools(self, custom_tools: list[LLMTool] | None) -> dict[str, LLMTool]:

        def pin_to_context(information: str) -> str:
            information_id = self._agent_context.pin_to_context(information)
            return f"Pinned successfully. id={information_id}"

        def unpin_to_context(information_id) -> str:
            self._agent_context.unpin_to_context(information_id)
            return f"Unpinned {information_id} successfully."

        tools = {
            'pin_to_context': LLMTool(
                function=pin_to_context,
                description='Pin a piece of information to keep it visible at the beginning of the context.',
                arguments=[
                    ToolArgument(
                        name='information',
                        description='Synthetic information to remember',
                        placeholder='[omitted - already inserted into pinned information]',
                        type=ArgumentType.STRING
                    )
                ]
            ),
            'unpin_to_context': LLMTool(
                function=unpin_to_context,
                description='Remove a previously pinned piece of information from the context.',
                arguments=[
                    ToolArgument(
                        name='information_id',
                        description='information_id that you want to unpin',
                        type=ArgumentType.STRING
                    )
                ]
            )
        }

        if custom_tools is None:
            return tools

        for tool in custom_tools:
            if tool.name in tools:
                raise ValueError(f'Tool name collision detected: {tool.name}')

            tools[tool.name] = tool

        return tools

    def _update_tools(self, custom_tools: list[LLMTool]) -> None:
        new_tools = self._init_tools(custom_tools)

        self._tools = new_tools
        self._agent_context._tools = new_tools

    async def _call_llm_client(self) -> LLMResponse:
        await self._agent_context.compact_if_needed()
        tools = list(self._tools.values())
        raw_response = await self._llm_client.async_generate(self._agent_context.context, self._tracker, tools)

        self._agent_context.add_to_context(raw_response.to_llm_message())

        return await self._handle_tool_call(raw_response)

    async def _handle_tool_call(self, response: LLMResponse) -> LLMResponse:
        if response.tool_calls is None:
            return response

        for index, tool_call in enumerate(response.tool_calls):
            content = self._compute_tool_call(tool_call)
            self._agent_context.add_to_context(
                LLMMessage(
                    role=LLMMessageRole.TOOL_RESULT,
                    content=content,
                    tool_calls=[tool_call]
                ),
                update_token_count = index == len(response.tool_calls) -1
            )

        return await self._call_llm_client()

    def _compute_tool_call(self, tool_call: LLMToolCall) -> str:
        assert self._tools is not None
        tool = self._tools.get(tool_call.name, None)
        if tool is None:
            return f"The tool {tool_call.name} doesn't exists"

        valid_args = inspect.signature(tool.function).parameters
        filtered_args = {
            argument: tool_call.arguments[argument]
            for argument in tool_call.arguments.keys() & valid_args.keys()
        }

        try:
            result = tool(filtered_args)
        except Exception as error:
            result = error

        content = _serialize_content(result)

        logger.debug(f'{tool_call.name} called with {filtered_args} : {content}')

        return content

    @abstractmethod
    def _build_starting_prompt(self) -> str:
        pass

def _serialize_content(result: Any) -> str:
    if isinstance(result, list):
        return str([str(item) for item in result])

    if isinstance(result, dict):
        return json.dumps(result)

    return str(result)
