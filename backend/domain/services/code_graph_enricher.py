import asyncio

from collections.abc import Callable

from loguru import logger

from backend.application.ports.graph_engine import GraphEngine
from backend.application.ports.llm_client import LLMClient
from backend.application.ports.llm_tokenizer import LLMTokenizer
from backend.application.ports.progress_reporter import ProgressEventType, ProgressReporter
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.llm_message import LLMMessage
from backend.domain.entities.llm_synthesis import LLMSynthesis
from backend.domain.services.context_resolver import ContextResolver
from backend.domain.services.prompt_factory import PromptFactory
from backend.domain.usage.llm_usage_tracker import LLMUsageTracker


class NodeDispatcher:

    def __init__(
            self,
            queue: asyncio.Queue[tuple[CodeNode, list[LLMMessage] ] | None],
            node_to_number_of_unhandled_dependencies: dict[CodeNode, int],
            node_id_to_parents: dict[str, list[CodeNode]],
            context_resolver: ContextResolver,
            prompt_factory: PromptFactory,
            llm_tokenizer: LLMTokenizer,
            number_of_workers: int,
            min_messages_tokens: int
    ):
        self._queue = queue
        self._node_to_number_of_unhandled_dependencies = node_to_number_of_unhandled_dependencies
        self._node_id_to_parents = node_id_to_parents
        self._context_resolver = context_resolver
        self._prompt_factory = prompt_factory
        self._llm_tokenizer = llm_tokenizer
        self._number_of_workers = number_of_workers
        self._min_messages_tokens = min_messages_tokens

    async def scan(self) -> None:
        node_pushed = []
        has_ineligible_node: bool = False

        if len(self._node_to_number_of_unhandled_dependencies) == 0:
            for _ in range(self._number_of_workers):
                await self._queue.put(None)
            return

        for node, number_of_unhandled_children in self._node_to_number_of_unhandled_dependencies.items():

            if number_of_unhandled_children != 0:
                continue

            messages = self._build_llm_messages(node, self._context_resolver)

            if self._is_eligible_to_llm_synthesis(node, self._node_id_to_parents, messages):
                await self._queue.put((node, messages))
                logger.debug(f"{node.code_block.fqn} Added to the queue to be treated by LLM ")
            else:
                self.remove_unhandled_dependencies_from_parents(node)
                has_ineligible_node = True

            node_pushed.append(node)

        logger.debug(f'{len(node_pushed)} Added in this scan - {len(self._node_to_number_of_unhandled_dependencies)} Remaining - {self._queue.qsize()} Elements in the queue')

        is_enrichment_finished = len(self._node_to_number_of_unhandled_dependencies) == 0
        if len(node_pushed) == 0 and self._queue.qsize() == 0 and not is_enrichment_finished:
            node = self._find_node_with_minimal_dependency_left()
            messages = self._build_llm_messages(node, self._context_resolver)
            await self._queue.put((node, messages))
            node_pushed.append(node)
            logger.debug(f"{node.code_block.fqn} Added to the queue to unlock enrichment process")

        for node in node_pushed:
            self._node_to_number_of_unhandled_dependencies.pop(node)

        if has_ineligible_node:
            await self.scan()

        return

    def _find_node_with_minimal_dependency_left(self) -> CodeNode:
        min_dependency_left: int | None = None
        min_node: CodeNode | None = None
        for node, dependency_left in self._node_to_number_of_unhandled_dependencies.items():
            if dependency_left == 1:
                return node

            if min_dependency_left is None or min_dependency_left > dependency_left:
                min_dependency_left = dependency_left
                min_node = node

        assert min_node is not None
        return min_node

    def _build_llm_messages(self, node: CodeNode, context_resolver: ContextResolver) -> list[LLMMessage]:
        children = context_resolver.resolve_children(node)
        call_context = context_resolver.resolve_call_contexts(node)

        return self._prompt_factory.build_enrichment_prompt(node, children, call_context)

    def _is_eligible_to_llm_synthesis(
            self,
            node: CodeNode,
            node_id_to_parents: dict[str, list[CodeNode]],
            messages: list[LLMMessage]
    ) -> bool:
        parents = node_id_to_parents[node.id]
        if len(parents) == 0:
            return True

        tokens = self._llm_tokenizer.count_token(messages)
        if tokens < self._min_messages_tokens:
            logger.debug(f"{node.code_block.fqn} Isn't eligible for treatment by LLM ({tokens} < {self._min_messages_tokens})")
            return False

        return True

    def remove_unhandled_dependencies_from_parents(self, node: CodeNode) -> None:
        parents = self._node_id_to_parents[node.id]

        for parent in parents:
            if parent in self._node_to_number_of_unhandled_dependencies:
                self._node_to_number_of_unhandled_dependencies[parent] -= 1

        logger.debug(f'{node.code_block.fqn} releases a dependency to {len(parents)} nodes')
        return

class CodeGraphEnricher:
    def __init__(
            self,
            llm_client: LLMClient,
            llm_tokenizer: LLMTokenizer,
            prompt_factory: PromptFactory,
            concurrency_limit: int,
            min_messages_tokens: int
    ):
        self._llm_client = llm_client
        self._llm_tokenizer = llm_tokenizer
        self._prompt_factory = prompt_factory
        self._concurrency_limit = concurrency_limit
        self._min_messages_tokens = min_messages_tokens
        self._node_dispatcher: NodeDispatcher | None = None

    async def run(
            self,
            graph_engine: GraphEngine,
            graph_id: str,
            tracker: LLMUsageTracker,
            progress_reporter: ProgressReporter
    ) -> None:
        logger.info('Start Graph Enrichment')
        await progress_reporter.report(ProgressEventType.ENRICHING_CODE_GRAPH)

        context_resolver = ContextResolver(graph_engine)

        node_id_to_parents: dict[str, list[CodeNode]] = {
            node.id: parent
            for node, parent in graph_engine.get_all_parents_by_node_by_graph(graph_id).items()
        }

        node_to_number_of_unhandled_dependencies: dict[CodeNode, int] = {
            node: len(children)
            for node, children in graph_engine.get_all_children_by_node_by_graph(graph_id).items()
        }

        await self._orchestrate_enrichment(
            context_resolver,
            node_id_to_parents,
            node_to_number_of_unhandled_dependencies,
            graph_engine.update_node,
            tracker
        )

        await progress_reporter.report(ProgressEventType.CODE_GRAPH_ENRICHED)

        return

    async def _orchestrate_enrichment(
            self,
            context_resolver: ContextResolver,
            node_id_to_parents: dict[str, list[CodeNode]],
            node_to_number_of_unhandled_dependencies: dict[CodeNode, int],
            update_function: Callable[[CodeNode], None],
            tracker
    ) -> None:
        semaphore = asyncio.Semaphore(self._concurrency_limit)
        queue: asyncio.Queue[tuple[CodeNode, list[LLMMessage] ] | None] = asyncio.Queue()

        self._node_dispatcher = NodeDispatcher(
            queue=queue,
            node_to_number_of_unhandled_dependencies=node_to_number_of_unhandled_dependencies,
            node_id_to_parents=node_id_to_parents,
            context_resolver=context_resolver,
            prompt_factory=self._prompt_factory,
            llm_tokenizer=self._llm_tokenizer,
            number_of_workers=self._concurrency_limit,
            min_messages_tokens=self._min_messages_tokens
        )

        assert self._node_dispatcher is not None
        await self._node_dispatcher.scan()

        node_workers = [asyncio.create_task(self._enrich_node(
            semaphore,
            queue,
            update_function,
            tracker
        )) for _ in range(self._concurrency_limit)]

        await asyncio.gather(*node_workers)

        self._node_dispatcher = None
        return

    async def _enrich_node(
            self,
            semaphore: asyncio.Semaphore,
            queue: asyncio.Queue[tuple[CodeNode, list[LLMMessage]] | None],
            update_function: Callable[[CodeNode], None],
            tracker: LLMUsageTracker
    ) -> None:

        while True:
            item: tuple[CodeNode, list[LLMMessage] ] | None = await queue.get()

            if item is None:
                logger.debug('Worker Stopped')
                break

            node, messages = item

            await self._build_llm_synthesis(semaphore, node, messages, update_function, tracker)
            assert self._node_dispatcher is not None
            self._node_dispatcher.remove_unhandled_dependencies_from_parents(node)
            await self._node_dispatcher.scan()

        return

    async def _build_llm_synthesis(
            self,
            semaphore: asyncio.Semaphore,
            node: CodeNode,
            messages: list[LLMMessage],
            update_function: Callable[[CodeNode], None],
            tracker: LLMUsageTracker
    ) -> None:
        async with (semaphore):
            llm_structured_response = await self._llm_client.async_generate_structured(messages, LLMSynthesis, tracker)

        llm_synthesis = llm_structured_response.data
        if llm_synthesis is None:
            return

        node.llm_synthesis = llm_synthesis
        update_function(node)

        logger.debug(f"Node: {node.code_block.fqn} \n"
                     f"Prompt {llm_structured_response.prompt_token_count} tok : {"\n".join([message.model_dump_json(indent=2) for message in messages])} \n"
                     f"Responses {llm_structured_response.completion_token_count} tok : {llm_synthesis.model_dump_json(indent=2)} \n")

        return
