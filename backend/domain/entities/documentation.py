from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel, model_validator


class DocumentationStatus(Enum):
    DRAFT = 'draft'
    FINISHED = 'finished'

class Documentation(BaseModel):
    documentation_id: str
    documentation_name: str
    additional_name: str | None
    fetched_date: datetime
    status: DocumentationStatus
    call_used: int
    input_token_used: int
    output_token_used: int
    hash: int

class DocumentationCreate(BaseModel):
    documentation_id: str
    documentation_name: str
    fetched_date: datetime
    additional_name: str | None = None
    hash: int

class DocumentationUpdate(BaseModel):
    documentation_name: str | None = None
    additional_name: str | None = None
    status: DocumentationStatus | None = None
    call_used: int | None = None
    input_token_used: int | None = None
    output_token_used: int | None = None

    @model_validator(mode='after')
    def check_at_least_one_field_is_not_none(self) -> Self:
        if all(value is None for value in self.model_dump().values()):
            raise ValueError('All value in documentation update can not be none')
        return self

