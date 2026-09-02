from abc import ABC, abstractmethod
from pathlib import Path

from backend.domain.entities.source_code import SourceCode


class SourceCodeProvider(ABC):

    @abstractmethod
    def retrieve_source_code_from_folder(self, path: Path) -> list[SourceCode]:
        pass

    @abstractmethod
    def valid_filepath(self, path: Path) -> set[Path]:
        pass

    @abstractmethod
    def get_sys_path(self, path: Path) -> list[Path]:
        pass
