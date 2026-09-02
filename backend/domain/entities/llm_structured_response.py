from typing import Generic, TypeVar

from pydantic import BaseModel

Template = TypeVar("Template", bound=BaseModel)

class LLMStructuredResponse(BaseModel, Generic[Template]):
    data: Template | None
    prompt_token_count: int
    completion_token_count: int
