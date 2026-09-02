from pathlib import Path

from backend.application.ports.linker import Linker
from backend.domain.enums.supported_language import SupportedLanguage
from backend.infrastructure.adapters.linker.default_linker import DefaultLinker
from backend.infrastructure.adapters.linker.jedi_linker import JediLinker


class LinkerProvider:

    @staticmethod
    def from_language_paths(
            language: SupportedLanguage,
            project_path: Path,
            accepted_files: set[Path]
    ) -> Linker:
        match language:
            case SupportedLanguage.PYTHON:
                return JediLinker.from_project_path(project_path, accepted_files)
            case SupportedLanguage.DEFAULT:
                return DefaultLinker()
