from pydantic import BaseModel

from backend.domain.entities.code_block import CodeBlock
from backend.domain.entities.llm_synthesis import LLMSynthesis


class CodeNode(BaseModel):
    graph_id: str
    id: str
    code_block: CodeBlock
    llm_synthesis: LLMSynthesis | None = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return str(self.model_dump())
