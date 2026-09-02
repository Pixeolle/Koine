from collections.abc import Awaitable, Callable
from pathlib import Path

from backend.application.enums.supported_platform import SupportedPlatform
from backend.application.ports.source_code_provider import SourceCodeProvider
from backend.application.ports.repository_fetcher import RepositoryFetcher
from backend.application.use_cases.ingest_repository_use_case import IngestRepositoryUseCase
from backend.core.settings import settings
from backend.domain.entities.repository_url import RepositoryURL
from backend.domain.entities.repository_status import RepositoryStatus
from backend.infrastructure.adapters.source_code_provider.archive_source_code_provider import ArchiveSourceCodeProvider
from backend.infrastructure.adapters.repository_fetcher.repository_fetcher_provider import RepositoryFetcherProvider


def build_ingest_repository_use_case() -> IngestRepositoryUseCase:
    source_code_provider = build_source_code_provider()

    return IngestRepositoryUseCase(
        temporary_path=settings.directory.temporary_path,
        source_code_provider=source_code_provider
    )

def build_source_code_provider() -> SourceCodeProvider:
    with Path.open(settings.directory.fileignore_filename, 'r') as reader:
        excluded_patern = [line.strip() for line in reader.readlines() if len(line.strip()) > 0]

    return ArchiveSourceCodeProvider(
        excluded_patern=excluded_patern
    )

def build_repositor_fetcher(platform: SupportedPlatform) -> RepositoryFetcher:
    return RepositoryFetcherProvider.from_platform_and_path(
        platform=platform,
        temporary_path=settings.directory.temporary_path
    )

def build_check_repository_available() -> Callable[[RepositoryURL], Awaitable[RepositoryStatus]]:
    async def is_repository_accessible(repository_url: RepositoryURL) -> RepositoryStatus:
        repository_fetcher = RepositoryFetcherProvider.from_platform_and_path(
            repository_url.platform,
            settings.directory.temporary_path
        )

        return await repository_fetcher.check_repository_availability(repository_url)

    return is_repository_accessible