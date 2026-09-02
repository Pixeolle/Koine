from functools import reduce

from backend.application.ports.graph_engine import GraphEngine
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.llm_tool import ArgumentType, LLMTool, ToolArgument
from backend.domain.enums.dependency_type import DependencyType


class GraphEngineToolProvider:

    def __init__(self, graph_engine: GraphEngine):
        self.graph_engine = graph_engine
        self.argument_library: dict[str, ToolArgument] = {
            'node_id': ToolArgument(
                name='node_id',
                type=ArgumentType.STRING,
                description='Id of the node to retrieve.'
            )
        }

    def get_get_root_nodes(self, graph_id: str) -> LLMTool:

        def get_root_nodes() -> dict[str, dict[str, str] ]:
            return reduce(
                _merge_dict,
                [_serialize_node(root_node) for root_node in self.graph_engine.get_root_nodes(graph_id)],
                {}
            )

        return LLMTool(
            function=get_root_nodes,
            description=(
                "Get every root node of the graph - nodes with no parent, i.e. top-level modules or entry points. Use "
                "this as your starting point to explore the codebase structure before drilling down into "
                "specific nodes."
            ),
            arguments=[]
        )

    def get_get_node_synthesis(self, graph_id: str) -> LLMTool:

        def get_node_synthesis(node_id: str) -> str:
            node = self.graph_engine.get_node(graph_id, node_id)

            if node is None:
                return "This node_id doesn't exist"

            if node.llm_synthesis is None:
                return (
                    "This node has no synthesis - together with its children, its content stayed under the threshold "
                    "for generating one. The information may be split across several small pieces rather than "
                    "concentrated here: read this node's own content with get_node_content, then use get_children to "
                    "find what's beneath it and read those individually too."
                )

            return str(node.llm_synthesis)

        return LLMTool(
            function=get_node_synthesis,
            description=(
                "Get the LLM-generated synthesis of a node - it summarizes both the node itself and everything "
                "beneath it in the graph (its children). This is your default way to understand a subtree: one call "
                "covers far more ground than reading nodes individually. Some nodes have no synthesis, meaning their "
                "content together with their children's stayed small enough not to need one - in that case, explore "
                "node and its children individually instead."
            ),
            arguments=[
                self.argument_library['node_id']
            ]
        )

    def get_get_node_content(self, graph_id: str) -> LLMTool:

        def get_node_content(node_id: str) -> str:
            node = self.graph_engine.get_node(graph_id, node_id)

            if node is None:
                return "This node_id doesn't exist"

            return str(node.code_block)

        return LLMTool(
            function=get_node_content,
            description=(
                "Get the raw source content of a single node only- not its children. Prefer get_node_synthesis first, "
                "since it covers this node's entire subtree in one call. Use this tool to verify a precis detail "
                "(an exact signature, a specific wording) or when a node has no synthesis at all."
            ),
            arguments=[
                self.argument_library['node_id']
            ]
        )

    def get_get_children(self) -> LLMTool:

        def get_children(node_id: str) -> dict[str, dict[str, str] ]:
            return reduce(
                _merge_dict,
                [_serialize_node(child) for child in self.graph_engine.get_children_from_node_id(node_id)],
                {}
            )

        return LLMTool(
            function=get_children,
            description=(
                "Get the direct children of a node - e.g. the methods of a class, or the classes/functions of a "
                "modules. Use this to navigate deeper into the codebase structure starting from a root node or "
                "any node found so far."
            ),
            arguments=[
                self.argument_library['node_id']
            ]
        )

    def get_get_parents(self) -> LLMTool:

        def get_parents(node_id: str, relation_type: str) -> dict[str, dict[str, str] ] | str:
            try:
                dependency_type = DependencyType(relation_type)
            except ValueError:
                return f"'{relation_type}' is not a valid relation type."

            return reduce(
                _merge_dict,
                [
                    _serialize_node(parent)
                    for parent in self.graph_engine.get_parent_from_node_id(node_id, dependency_type)
                ],
                {}
            )

        return LLMTool(
            function=get_parents,
            description=(
                "Get the parent nodes of a node, following either call relationships (its callers) or structural "
                "relationship (its containing class/module) - see relation_type."
            ),
            arguments=[
                self.argument_library['node_id'],
                ToolArgument(
                    name='relation_type',
                    type=ArgumentType.ENUM,
                    description=(
                        "Which kind of parent relationship to follow. 'call' finds nodes that call this one "
                        "(its callers). 'structural' finds the containing node (e.g. the class that defines this "
                        "method, or the module that contains this class)."
                    ),
                    enum=DependencyType.values()
                )
            ]
        )


def _serialize_node(node: CodeNode) -> dict[str, dict[str, str] ]:
    return {
        node.id : {
            'fqn': node.code_block.fqn,
            'signature': node.code_block.signature.signature or ''
        }
    }

def _merge_dict(first_dict: dict, second_dict: dict) -> dict:
    return first_dict | second_dict
