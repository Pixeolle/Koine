from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.application.mappers.create_code_block import CreateCodeBlock
from backend.domain.entities.code_node import CodeNode


class CreateCodeNode:

    @staticmethod
    def from_parsed_code_block(graph_id: str, parsed_block_dto: ParsedBlockDTO) -> CodeNode:
        return CodeNode(
            graph_id=graph_id,
            id=parsed_block_dto.id,
            code_block=CreateCodeBlock.from_parsed_block_dto(parsed_block_dto)
        )
