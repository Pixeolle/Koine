from typing import Any

from pydantic import BaseModel


class LLMToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]
