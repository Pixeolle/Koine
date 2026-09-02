from abc import ABC, abstractmethod
from pathlib import Path

from backend.domain.entities.repository_informations import RepositoryInformations
from backend.domain.entities.repository_url import RepositoryURL
from backend.domain.entities.repository_status import RepositoryStatus


class RepositoryFetcher(ABC):

    @abstractmethod
    async def fetch_code(self, repository_url: RepositoryURL) -> Path:
        pass

    @staticmethod
    @abstractmethod
    def extract_repository_informations(repository_url: RepositoryURL) -> RepositoryInformations:
        pass

    @abstractmethod
    async def check_repository_availability(self, repository_url: RepositoryURL) -> RepositoryStatus:
        pass
