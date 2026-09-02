import re

from pathlib import Path

from backend.application.dtos.parsed_block_dto import ParsedBlockDTO
from backend.domain.entities.code_block import CodeBlock


class CreateCodeBlock:

    @staticmethod
    def from_parsed_block_dto(parsed_block_dto: ParsedBlockDTO) -> CodeBlock:
        fqn = _resolve_fqn(parsed_block_dto)
        sanitized_source_code = _sanitize_source_code(parsed_block_dto.raw_bytes)

        return CodeBlock(
            fqn = fqn,
            name=parsed_block_dto.name,
            type=parsed_block_dto.type,
            signature=parsed_block_dto.signature,
            source_code=sanitized_source_code,
        )

def _sanitize_source_code(source_code: bytes) -> str:
    string_source_code = str(source_code.decode('utf8'))
    return re.sub(r'\r\n\r\n(?:[ \t]*\r\n)+', '\r\n\r\n', string_source_code.strip())

def _resolve_fqn(block_dto: ParsedBlockDTO) -> str:
    path_fqn = _path_to_fqn(block_dto.path)
    file_fqn = block_dto.local_fqn

    if file_fqn is None:
        return path_fqn

    return f'{path_fqn}.{file_fqn}'

def _path_to_fqn(path: Path) -> str:
    path_without_extension = re.sub('[.][^.]*$', '', string=str(path))
    return re.sub('[\\\\]', '.', string=path_without_extension)
