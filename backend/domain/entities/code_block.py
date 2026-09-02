from pydantic import BaseModel, ConfigDict

from backend.domain.entities.signature_node import SignatureNode
from backend.domain.enums.code_block_type import CodeBlockType


class CodeBlock(BaseModel):
    model_config = ConfigDict(frozen=True)

    fqn : str
    name: str
    type: CodeBlockType
    signature: SignatureNode
    source_code: str

    def __str__(self) -> str:
        return str(self.model_dump_json())

    def serialize(self) -> str:

        lines = [
            f"# === INLINE RAW CODE: {self.fqn} ===",
            f"# Node Type: {self.type}",
            "# Architecture Signature: ",
        ]

        for line in self.signature.render().splitlines():
            lines.append(f"# {line}")

        lines.extend([
            "# ",
        ])

        for line in self.source_code.splitlines():
            lines.append(f"{line}")

        return "\n".join(lines)
