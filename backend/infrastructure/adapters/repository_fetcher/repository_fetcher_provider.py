from pathlib import Path

from backend.application.enums.supported_platform import SupportedPlatform
from backend.application.ports.repository_fetcher import RepositoryFetcher
from backend.infrastructure.adapters.repository_fetcher.gitlab_api_adapter import GitLabAPIAdapter
from backend.infrastructure.network.http_client import HTTPClient


class RepositoryFetcherProvider:

    @staticmethod
    def from_platform_and_path(platform: SupportedPlatform, temporary_path: Path) -> RepositoryFetcher:
        match platform:
            case SupportedPlatform.GITLAB:
                http_client = HTTPClient()
                return GitLabAPIAdapter(
                    http_client=http_client,
                    temporary_path=temporary_path
                )
            case _:
                raise ValueError(f"{platform} not supported yet")
