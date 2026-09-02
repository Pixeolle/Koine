import uuid

from collections.abc import Callable
from string import Template
from typing import Literal

from backend.application.ports.llm_client import LLMClient
from backend.application.ports.llm_tokenizer import LLMTokenizer
from backend.domain.agents.base_agent_settings import BaseAgentParameters
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.entities.llm_tool import LLMTool
from backend.domain.entities.llm_tool_call import LLMToolCall
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


class AgentContext:

    def __init__(
            self,
            system_prompt: str,
            build_starting_prompt: Callable[[], str],
            tools: dict[str, LLMTool],
            tracker: LLMUsageTracker,
            base_settings: BaseAgentParameters,
    ):
        self._system_prompt = LLMMessage(role=LLMMessageRole.SYSTEM, content=system_prompt)
        self._build_starting_prompt = build_starting_prompt
        self._pinned_information: dict[str, str] = {}
        self._tools = tools
        self._tracker = tracker
        self._llm_client: LLMClient = base_settings.llm_client
        self._llm_tokenizer: LLMTokenizer = base_settings.llm_tokenizer

        self._context: list[LLMMessage] = [self._system_prompt, self._build_starting_message()]
        self._max_context_token_length = base_settings.max_context_token_length
        self._max_context_token_length_after_compression = base_settings.max_context_token_length_after_compression
        self._start_percentile_compression = base_settings.start_percentile_compression
        self._end_percentile_compression = base_settings.end_percentile_compression
        self._compression_system_prompt: Template = Template(base_settings.compression_system_prompt)

        self._is_pinned_message_inserted = False
        self._context_token_length = self._llm_tokenizer.count_token(self._context)

    def reset(self) -> None:
        self._context = [self._system_prompt, self._build_starting_message()]
        self._is_pinned_message_inserted = False
        self._pinned_information = {}

    def new_task(self) -> None:
        self._context = [self._system_prompt, self._build_starting_message()]
        self._is_pinned_message_inserted = False
        self._render_pinned_information()

    @property
    def context(self) -> list[LLMMessage]:
        return self._context.copy()

    def add_to_context(self, message: LLMMessage, update_token_count: bool = False) -> None:
        # if message.role is LLMMessageRole.TOOL_CALL:
            # self._delete_duplicate_llm_message(message)
            # self._replace_tool_calls_value_by_placeholder(message)

        self._context.append(message)
        if message.role in {LLMMessageRole.USER, LLMMessageRole.TOOL_RESULT} and update_token_count:
            self._context_token_length = self._llm_tokenizer.count_token(self._context)
        return

    def set_context_token_length(self, context_token_length: int) -> None:
        self._context_token_length = context_token_length

    def _delete_duplicate_llm_message(self, message: LLMMessage) -> None:
        assert message.tool_calls is not None

        new_tool_calls_hashed = {
            self._hash_tool_call(tool_call)
            for tool_call in message.tool_calls
            if tool_call.name in self._tools and self._tools[tool_call.name].can_be_deleted
        }

        if len(new_tool_calls_hashed) == 0:
            return

        empty_message_index: list[int] = []

        for index, context_message in enumerate(self._context):
            is_message_empty = self._delete_duplicate_tool_call_in_context_message(
                context_message,
                new_tool_calls_hashed
            )
            if is_message_empty:
                empty_message_index.append(index)

        for index, index_to_delete in enumerate(empty_message_index):
            self._context.pop(index_to_delete - index)
        return

    def _delete_duplicate_tool_call_in_context_message(
            self,
            context_message: LLMMessage,
            new_tool_calls_hashed: set[str]
    ) -> bool:
        if context_message.role not in {LLMMessageRole.TOOL_CALL, LLMMessageRole.TOOL_RESULT}:
            return False

        assert context_message.tool_calls is not None

        duplicate_tool_call_index: list[int] = []
        for index, tool_call in enumerate(context_message.tool_calls):
            if self._hash_tool_call(tool_call) in new_tool_calls_hashed:
                duplicate_tool_call_index.append(index)

        for index, index_to_delete in enumerate(duplicate_tool_call_index):
            context_message.tool_calls.pop(index_to_delete - index)

        is_tool_call_empty = len(context_message.tool_calls) == 0 and len(context_message.content) == 0
        is_tool_result_empty = len(context_message.tool_calls) == 0
        should_be_deleted = (context_message.role is LLMMessageRole.TOOL_CALL and is_tool_call_empty or
                             context_message.role is LLMMessageRole.TOOL_RESULT and is_tool_result_empty)
        return should_be_deleted

    def _hash_tool_call(self, tool_call: LLMToolCall) -> str:
        tool = self._tools.get(tool_call.name, None)

        if tool is None:
            raise ValueError(f"The tool {tool_call.name} doesn't exists")

        return (
            f'{tool.name}::'
            f'{"#".join(f"{
            str(argument)}:{str(value)}"
                        for argument, value in tool_call.arguments.items()
                        if argument in tool.discriminating_argument_names
                        )}'
        )

    def _replace_tool_calls_value_by_placeholder(self, message: LLMMessage) -> None:
        assert message.tool_calls is not None

        for tool_call in message.tool_calls:
            if tool_call.name in self._tools:
                self._replace_tool_call_values_by_placeholder(tool_call)

        return

    def _replace_tool_call_values_by_placeholder(self, tool_call: LLMToolCall) -> None:
        tool = self._tools[tool_call.name]

        for argument in tool.arguments:
            if argument.placeholder is None:
                continue

            tool_call.arguments[argument.name] = argument.placeholder
        return

    def pin_to_context(self, information: str) -> str:
        information_id = str(uuid.uuid4())
        self._pinned_information[information_id] = information
        self._render_pinned_information()

        return information_id

    def unpin_to_context(self, information_id: str) -> None:
        if information_id not in self._pinned_information:
            raise ValueError(f"{information_id} doesn't exist in the pinned information")
        self._pinned_information.pop(information_id)
        self._render_pinned_information()

    def _update_pinned_information(self) -> None:
        if len(self._pinned_information) == 0:
            if self._is_pinned_message_inserted:
                self._context.pop(1)
                self._is_pinned_message_inserted = False
            return

        pinned_information = self._render_pinned_information()
        information_message = LLMMessage(
            role=LLMMessageRole.USER,
            content=pinned_information
        )

        if self._is_pinned_message_inserted:
            self._context[1] = information_message
        else:
            self._context.insert(1, information_message)
            self._is_pinned_message_inserted = True
        return

    def _render_pinned_information(self) -> str:
        pinned_information = "\n\n".join(
            f"<pinned_information id={information_id}>\n{information}\n</pinned_information>"
            for information_id, information in self._pinned_information.items()
        )

        return (
            "<pinned_context>\n"
            "The following is reference material you chose to retain via pin_to_context. "
            "It is not a message from the user - treat it as background information only. \n\n"
            f"{pinned_information}\n\n"
            f"</pinned_context>"
        )

    async def compact_if_needed(self) -> None:
        if self._context_token_length <= self._max_context_token_length:
            return

        start_index_mutable_message = 3 if self._is_pinned_message_inserted else 2
        end_index_mutable_message = self._find_last_index_mutable_message()
        start_index_compression = max(
            start_index_mutable_message,
            self._find_percentile_index(self._start_percentile_compression)
        )
        end_index_compression = min(
            end_index_mutable_message,
            self._find_percentile_index(self._end_percentile_compression, convention='before')
        )

        messages_to_compress, message_to_keep_before, message_to_keep_after = self._split_context(
            start_index_compression,
            end_index_compression
        )

        immutable_context = message_to_keep_before + message_to_keep_after
        base_token_length = self._llm_tokenizer.count_token(immutable_context)
        compression_target_token_length = self._max_context_token_length_after_compression - base_token_length

        compressed_context = await self._compress_context(messages_to_compress, compression_target_token_length)

        self._context = message_to_keep_before + [compressed_context] + message_to_keep_after
        return

    def _find_percentile_index(self, percentile: int, convention: Literal['before', 'after'] = 'after') -> int:
        percentile_threshold = int(float(self._context_token_length * percentile) / 100)
        cumulative_token_length = 0

        previous_valid_index = 0

        for index, message in enumerate(self._context):
            cumulative_token_length += self._llm_tokenizer.count_token(message)

            if message.role is LLMMessageRole.TOOL_RESULT:
                continue

            if cumulative_token_length > percentile_threshold:
                return index if convention == 'after' else previous_valid_index

            previous_valid_index = index

        return len(self._context) - 1

    def _find_last_index_mutable_message(self) -> int:
        for index in range(len(self._context) - 2, -1, -1):
            if self._context[index].role is not LLMMessageRole.TOOL_RESULT:
                return index - 1

        return 0

    def _split_context(
            self,
            start_index_compression: int,
            end_index_compression: int
    ) -> tuple[list[LLMMessage], list[LLMMessage], list[LLMMessage]]:
        if start_index_compression >= end_index_compression:
            raise ValueError("Start index can't be superior to end index")

        message_to_compress: list[LLMMessage] = []
        message_to_keep_before: list[LLMMessage] = []
        message_to_keep_after: list[LLMMessage] = []

        for index in range(len(self._context)):
            if start_index_compression > index:
                message_to_keep_before.append(self._context[index])
            elif start_index_compression <= index <= end_index_compression:
                message_to_compress.append(self._context[index])
            else:
                message_to_keep_after.append(self._context[index])

        return message_to_compress, message_to_keep_before, message_to_keep_after

    async def _compress_context(self, messages_to_compress: list[LLMMessage], compression_target: int) -> LLMMessage:
        def is_context_compressed(compressed_context: LLMMessage | None) -> bool:
            if compressed_context is None:
                return False

            return self._llm_tokenizer.count_token(compressed_context) < compression_target

        def compressed_content_to_message(compressed_content: str) -> LLMMessage:
            return LLMMessage(
                role=LLMMessageRole.USER,
                content=(
                    f"<compacted_context>\n"
                    f"The following is an automatically generated summary of earlier exploration, "
                    f"compressed to save space. It is not a message from the user .\n\n"
                    f"{compressed_content}"
                    f"</compacted_context>"
                )
            )

        compressed_context: LLMMessage | None = None
        compression_target_adjusted: int = compression_target

        while not is_context_compressed(compressed_context):
            compression_prompt = self._build_compression_prompt(messages_to_compress, compression_target_adjusted)
            compressed_content = await self._llm_client.async_generate(
                compression_prompt,
                self._tracker
            )
            compressed_context = compressed_content_to_message(compressed_content.content)
            compression_target_adjusted = int(compression_target_adjusted * 0.99 - 1)

        assert compressed_context is not None
        return compressed_context

    def _build_compression_prompt(
            self,
            messages_to_compress: list[LLMMessage],
            compression_target: int
    ) -> list[LLMMessage]:
        return [
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=self._compression_system_prompt.substitute({
                    'pinned_context_block': self._render_pinned_information(),
                    'target_tokens': compression_target
                })
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=f"<transcript_to_compact>\n"
                        f"{_serialize_messages(messages_to_compress)}\n"
                        f"</transcript_to_compact>"
            )
        ]

    def _build_starting_message(self) -> LLMMessage:
        return LLMMessage(
            role=LLMMessageRole.USER,
            content=self._build_starting_prompt()
        )


def _serialize_messages(messages: list[LLMMessage]) -> str:
    serialized_messages: list[str] = []

    for message in messages:
        serialized_message = _serialize_message(message)
        if serialized_message is None:
            continue

        if isinstance(serialized_message, str):
            serialized_messages.append(serialized_message)
        else:
            serialized_messages.extend(serialized_message)
    return "\n".join(serialized_messages)

def _serialize_message(message: LLMMessage) -> list[str] | str | None:
    match message.role:
        case LLMMessageRole.SYSTEM:
            return None

        case LLMMessageRole.USER:
            return f"[user] {message.content}"

        case LLMMessageRole.ASSISTANT:
            return f"[assistant] {message.content}"

        case LLMMessageRole.TOOL_CALL:
            assert message.tool_calls is not None
            return [
                f"[called {tool_call.name}({tool_call.arguments})]"
                for tool_call in message.tool_calls
            ]

        case LLMMessageRole.TOOL_RESULT:
            return f"[result] {message.content}"
