from pydantic import BaseModel, ConfigDict


class UnresolvedDependencyDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    parsed_block_id: str
    line: int
    column: int
    start_byte: int
    end_byte: int
