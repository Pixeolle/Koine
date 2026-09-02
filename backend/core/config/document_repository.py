from pathlib import Path
from typing import Self

from pydantic import BaseModel, PrivateAttr, computed_field, model_validator


class DocumentRepositorySettings(BaseModel):
    sqlite_filepath: Path
    sqlite_directory: Path

    _outputs_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent.parent / 'outputs')

    @computed_field
    @property
    def sqlite_path(self) -> Path:
        return self._outputs_path / self.sqlite_directory

    @model_validator(mode='after')
    def create_directory(self) -> Self:
        sqlite_directory = self._outputs_path / self.sqlite_directory
        sqlite_directory.mkdir(parents=True, exist_ok=True)

        return self
