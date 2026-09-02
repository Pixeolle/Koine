from datetime import datetime

from pydantic import BaseModel

from backend.domain.entities.documentation import Documentation
from backend.domain.entities.document import Document, DocumentStatus


class DocumentationSummary(BaseModel):
    documentation_id: str
    documentation_name: str
    additional_name: str | None
    fetched_date: datetime
    input_token_used: int
    output_token_used: int

    @classmethod
    def from_domain(cls, documentation: Documentation) -> "DocumentationSummary":
        return cls(
            documentation_id=documentation.documentation_id,
            documentation_name=documentation.documentation_name,
            additional_name=documentation.additional_name,
            fetched_date=documentation.fetched_date,
            input_token_used=documentation.input_token_used,
            output_token_used=documentation.output_token_used
        )


class DocumentSummary(BaseModel):
    document_name: str
    goal: str
    status: DocumentStatus = DocumentStatus.DRAFT
    review: str = ''
    iteration: int = 0
    source_node_ids: list[str] = []

    @classmethod
    def from_domain(cls, document: Document) -> "DocumentSummary":
        return cls(
            document_name=document.document_name,
            goal=document.goal,
            status=document.status,
            review=document.review,
            iteration=document.iteration,
            source_node_ids=document.source_node_ids
        )

class DocumentResponse(BaseModel):
    document_name: str
    content: str

    @classmethod
    def from_domain(cls, document: Document) -> "DocumentResponse":
        return cls(
            document_name=document.document_name,
            content=document.content
        )
