import re

from abc import ABC, abstractmethod
from pathlib import Path
from zipfile import BadZipFile, LargeZipFile, ZipFile

from backend.application.ports.repository_fetcher import RepositoryFetcher
from backend.domain.entities.repository_url import RepositoryURL
from backend.domain.entities.repository_status import RepositoryStatus
from backend.domain.exceptions.file_system_error import FileSystemError
from backend.infrastructure.network.http_client import HTTPClient
from backend.infrastructure.network.type_request import TypeRequest


class BaseGitAdapter(RepositoryFetcher, ABC):
    def __init__(self, http_client: HTTPClient, temporary_path: Path):
        self.http_client = http_client
        self.temporary_path = temporary_path

    async def fetch_code(self, repository_url: RepositoryURL) -> Path:
        api_url = self._build_api_url(repository_url)

        archive_path = await self._download_archive(api_url, repository_url.headers)
        return self._extract_archive(archive_path)

    async def check_repository_availability(self, repository_url: RepositoryURL) -> RepositoryStatus:
        api_url = self._build_api_url(repository_url)
        try:
            async with self.http_client as http:
                response = await http.request(TypeRequest.HEAD, api_url, headers=repository_url.headers)
        except Exception as _:
            return RepositoryStatus(is_available=False)

        content_filename = _get_filename(response.headers['content-disposition'])

        return RepositoryStatus(is_available=True, content_filename=content_filename)

    @staticmethod
    @abstractmethod
    def _build_api_url(repository_url: RepositoryURL) -> str:
        pass

    async def _download_archive(self, api_url: str, headers: dict[str, str] | None) -> Path:
        async with self.http_client as http:
            response = await http.request(TypeRequest.GET, api_url, headers=headers)

        file_name = _get_filename(response.headers['content-disposition'])
        destination_path = self.temporary_path / file_name
        try:
            with Path.open(destination_path, 'wb') as file:
                file.write(response.content)
        except OSError as error:
            raise FileSystemError(destination_path, str(error)) from error

        return destination_path

    def _extract_archive(self, path: Path) -> Path:
        try:
            with ZipFile(path) as archive:
                archive.extractall(path=self.temporary_path)
        except (BadZipFile, LargeZipFile) as error:
            raise FileSystemError(path, str(error)) from error
        except Exception as error:
            raise FileSystemError(path, str(error)) from error
        finally:
            _remove_extracted_zip(path)

        return self.temporary_path / path.stem


def _get_filename(content_disposition: str) -> str:
    match = re.search('filename="([^"]*)"', content_disposition)
    if match:
        return match.group(1)
    return 'archive.zip'


def _remove_extracted_zip(path) -> None:
    try:
        Path.unlink(path)
    except OSError as error:
        raise FileSystemError(path, str(error)) from error
