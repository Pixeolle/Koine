from backend.application.ports.graph_engine import GraphEngine
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.llm_enrichment_input import CallContext, Child, RepresentationType
from backend.domain.enums.dependency_type import DependencyType


class ContextResolver:

    def __init__(self, graph_engine: GraphEngine):
        self.graph_engine = graph_engine

    def resolve_call_contexts(self, node: CodeNode) -> list[CallContext]:
        parents = self.graph_engine.get_parent_from_node(node, DependencyType.CALL)

        call_contexts: list[CallContext] = []
        for parent in parents:
            call_contexts.append(_resolve_call_context(parent))
        return call_contexts

    def resolve_children(self, node: CodeNode) -> list[Child]:
        children = self.graph_engine.get_children_from_node(node)

        children_context: list[Child] = []
        for child in children:
            children_context.append(self._resolve_child_context(child))

        return children_context

    def _resolve_child_context(self, child: CodeNode) -> Child:
        signature = child.code_block.signature.signature or "null"

        if child.llm_synthesis is not None:
            return Child(
                child_fqn=child.code_block.fqn,
                node_type=child.code_block.type.name,
                signature=signature,
                representation_type=RepresentationType.SUMMARY,
                content=child.llm_synthesis.serialize(child.code_block.fqn)
            )

        content = "\n".join(self._resolve_sub_children_content(child))

        return Child(
            child_fqn=child.code_block.fqn,
            node_type=child.code_block.type.name,
            signature=signature,
            representation_type=RepresentationType.RAW_CODE_WITH_INLINE_SUBCHILDREN,
            content=content
        )

    def _resolve_sub_children_content(
            self,
            child: CodeNode,
            node_already_encounter: set[CodeNode] | None = None
    ) -> set[str]:
        if child.llm_synthesis is not None:
            return {child.llm_synthesis.serialize(child.code_block.fqn)}

        if node_already_encounter is None:
            node_already_encounter = {child}

        children_of_child = set(self.graph_engine.get_children_from_node(child))
        children_of_child -= node_already_encounter
        node_already_encounter.update(children_of_child)

        contents: set[str] = {child.code_block.serialize()}

        for child_of_child in children_of_child:
            contents.update(self._resolve_sub_children_content(
                child_of_child,
                node_already_encounter=node_already_encounter
            ))

        return contents



def _resolve_call_context(parent: CodeNode) -> CallContext:
    return CallContext(
        context_fqn=parent.code_block.fqn,
        usage_snippet=parent.code_block.source_code
    )
