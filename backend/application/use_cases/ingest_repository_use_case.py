from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from backend.application.ports.progress_reporter import ProgressEventType, ProgressReporter
from backend.application.ports.source_code_provider import SourceCodeProvider
from backend.domain.entities.repository_url import RepositoryURL
from backend.domain.entities.source_code import SourceCode
from backend.infrastructure.adapters.repository_fetcher.repository_fetcher_provider import (
    RepositoryFetcherProvider,
)


class IngestOutput(BaseModel):
    source_codes: list[SourceCode]
    project_path: Path
    accepted_files: set[Path]
    repository_name: str
    branch_name: str | None
    fetched_date: datetime
    archive_filename: str

class IngestRepositoryUseCase:

    def __init__(self, temporary_path: Path, source_code_provider: SourceCodeProvider):
        self._temporary_path = temporary_path
        self._source_code_provider = source_code_provider

    async def ingest(self, repository_url: RepositoryURL, progress_reporter: ProgressReporter) -> IngestOutput:

        await progress_reporter.report(ProgressEventType.FETCHING)
        repository_fetcher = RepositoryFetcherProvider.from_platform_and_path(
            platform=repository_url.platform,
            temporary_path=self._temporary_path
        )

        path = await repository_fetcher.fetch_code(repository_url)

        source_codes = self._source_code_provider.retrieve_source_code_from_folder(path)
        await progress_reporter.report(
            ProgressEventType.REPOSITORY_FETCHED,
            file_len=len(source_codes)
        )

        accepted_files = self._source_code_provider.valid_filepath(path)
        repository_informations = repository_fetcher.extract_repository_informations(repository_url)

        return IngestOutput(
            source_codes=source_codes,
            project_path=path,
            accepted_files=accepted_files,
            repository_name=repository_informations.name,
            branch_name=repository_informations.branch,
            fetched_date=datetime.now(),
            archive_filename=path.name
        )
