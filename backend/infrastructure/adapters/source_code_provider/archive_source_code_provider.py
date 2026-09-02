from pathlib import Path

from pathspec import PathSpec

from backend.application.ports.source_code_provider import SourceCodeProvider
from backend.domain.entities.source_code import SourceCode
from backend.domain.exceptions.file_system_error import FileSystemError


class ArchiveSourceCodeProvider(SourceCodeProvider):

    def __init__(self, excluded_patern: list[str]):
        self._ignore_matcher = PathSpec.from_lines('gitignore',excluded_patern)

    def retrieve_source_code_from_folder(self, path: Path) -> list[SourceCode]:
        filepaths = self.valid_filepath(path)
        source_codes = []

        for filepath in filepaths:
            try:
                with Path.open(filepath, 'rb') as reader:
                    relative_path = filepath.relative_to(path.parent)
                    source_code = SourceCode(path=relative_path, source_code=reader.read())
                    source_codes.append(source_code)

            except OSError as error:
                raise FileSystemError(filepath, str(error)) from error

        return source_codes

    def valid_filepath(self, path: Path) -> set[Path]:
        excluded_files = {
            path / excluded_file
            for excluded_file in self._ignore_matcher.match_tree_files(path)}
        files = {path for path in path.glob('**/*') if path.is_file()}

        return files - excluded_files

    def get_sys_path(self, path: Path) -> list[Path]:
        return [
            directory
            for directory in path.iterdir()
            if directory.is_dir() and not self._ignore_matcher.match_file(str(directory.relative_to(path)) + '/')
        ]
