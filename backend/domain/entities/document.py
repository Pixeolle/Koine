from enum import Enum
from typing import Self

from pydantic import BaseModel, model_validator, computed_field


class DocumentStatus(Enum):
    DRAFT = 'draft'
    APPROVED = 'approved'

class Document(BaseModel):
    document_name: str
    documentation_id: str
    goal: str
    content: str = ''
    status: DocumentStatus = DocumentStatus.DRAFT
    review: str = ''
    iteration: int = 0
    source_node_ids: list[str] = []

    def __str__(self) -> str:
        excluded_fields = {'documentation_id'}

        if len(self.review) == 0:
            excluded_fields.add('review')

        return self.model_dump_json(exclude=excluded_fields)

    @staticmethod
    def build_document_id(documentation_id: str, document_name: str) -> str:
        return f'{documentation_id}::{document_name}'

class DocumentCreate(BaseModel):
    documentation_id: str
    document_name: str
    goal: str

    @computed_field
    @property
    def document_id(self) -> str:
        return Document.build_document_id(self.documentation_id, self.document_name)

class DocumentUpdate(BaseModel):
    goal: str | None = None
    content: str | None = None
    status: DocumentStatus | None = None
    review: str | None = None
    source_node_ids: list[str] | None = None

    @model_validator(mode='after')
    def check_at_least_one_field_is_not_none(self) -> Self:
        if all(value is None for value in self.model_dump().values()):
            raise ValueError('All value in document update can not be none')
        return self
