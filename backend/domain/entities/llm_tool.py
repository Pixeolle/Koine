from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, computed_field


class ArgumentType(Enum):
   STRING = 'string'
   NUMBER = 'number'
   INTEGER = 'integer'
   BOOLEAN = 'boolean'
   ARRAY = 'array'
   ENUM = 'enum'

class ToolArgument(BaseModel):
   name: str
   description: str
   type: ArgumentType

   placeholder: str | None = None
   required: bool = True
   is_discriminating: bool = True
   items: 'ToolArgument | None' = None
   enum: list[str] | None = None

class LLMTool(BaseModel):
   function: Callable
   description: str
   arguments: list[ToolArgument]
   can_be_deleted: bool = True

   @computed_field
   @property
   def name(self) -> str:
      return self.function.__name__

   def __call__(self, kwargs: dict[str, Any]):
      return self.function(**kwargs)

   @property

   def discriminating_argument_names(self) -> list[str]:
      return [argument.name for argument in self.arguments]
