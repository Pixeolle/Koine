from backend.domain.entities.code_block import CodeBlock
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.llm_synthesis import LLMSynthesis
from backend.infrastructure.adapters.graph_engines.neo4j.code_node_entity import CodeNodeEntity


class CodeNodeEntityMapper:

    @staticmethod
    def to_domain(code_node_entity: CodeNodeEntity) -> CodeNode:
        return CodeNode(
            graph_id=code_node_entity.graph_id,
            id=code_node_entity.code_node_id,
            code_block=CodeBlock.model_validate_json(code_node_entity.code_block),
            llm_synthesis=LLMSynthesis.model_validate_json(code_node_entity.llm_synthesis)
                if code_node_entity.llm_synthesis else None
        )

    @staticmethod
    def to_entity(code_node: CodeNode) -> CodeNodeEntity:
        return CodeNodeEntity(
            graph_id=code_node.graph_id,
            code_node_id=code_node.id,
            code_block=code_node.code_block.model_dump_json(),
            llm_synthesis=code_node.llm_synthesis.model_dump_json() if code_node.llm_synthesis else None
        )
