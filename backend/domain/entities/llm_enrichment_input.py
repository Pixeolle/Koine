from enum import Enum

from pydantic import BaseModel

from backend.domain.enums.code_block_type import CodeBlockType


class CallContext(BaseModel):
    context_fqn: str
    usage_snippet: str

class RepresentationType(Enum):
    SUMMARY = 'summary'
    RAW_CODE_WITH_INLINE_SUBCHILDREN = 'raw_code_with_inline_subchildren'

class Child(BaseModel):
    child_fqn: str
    node_type: str
    signature: str
    representation_type: RepresentationType
    content: str

class LLMEnrichmentInput(BaseModel):
    fqn: str
    node_type: CodeBlockType
    raw_code: str
    call_contexts: list[CallContext]
    children: list[Child]




