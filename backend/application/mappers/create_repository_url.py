from pydantic import BaseModel

from backend.application.enums.supported_platform import SupportedPlatform
from backend.domain.entities.repository_url import GitHubURL, GitLabURL, RepositoryURL
from backend.domain.exceptions.unsupported_platform_error import UnsupportedPlatformError
from backend.infrastructure.api.generations.schemas import GenerationRequest


class CreateRepositoryURL(BaseModel):

    @staticmethod
    def from_generation_request(generation_input: GenerationRequest) -> RepositoryURL:
        url = str(generation_input.url)

        match generation_input.platform:
            case SupportedPlatform.GITLAB:
                return GitLabURL(
                    url=url,
                    access_token=generation_input.access_token
                )

            case SupportedPlatform.GITHUB:
                return GitHubURL(
                   url=url,
                    access_token=generation_input.access_token
                )

            case _:
                raise UnsupportedPlatformError(url=url)
