import re

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, HttpUrl, TypeAdapter, field_validator

from backend.application.enums.supported_platform import SupportedPlatform


class RepositoryURL(ABC, BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    access_token: str | None = None

    @field_validator('url', mode='before')
    @classmethod
    def sanitize_url(cls, raw_url: str) -> str:
        adapter = TypeAdapter(HttpUrl)
        adapter.validate_python(raw_url)

        return re.sub(r"\.git$", "", raw_url).strip()

    @property
    @abstractmethod
    def platform(self) -> SupportedPlatform:
        pass

    @property
    def platform_name(self) -> str:
        return self.platform.platform_name

    @property
    @abstractmethod
    def headers(self) -> dict[str, str] | None:
        pass

class GitLabURL(RepositoryURL):

    @property
    def platform(self) -> SupportedPlatform:
        return SupportedPlatform.GITLAB

    @property
    def headers(self) -> dict[str, str] | None:
        if self.access_token is None:
            return None

        return {'PRIVATE-TOKEN': self.access_token}


class GitHubURL(RepositoryURL):

    @property
    def platform(self) -> SupportedPlatform:
        return SupportedPlatform.GITHUB

    @property
    def headers(self) -> dict[str, str] | None:
        return None
