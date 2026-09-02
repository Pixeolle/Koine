from pydantic import BaseModel, HttpUrl

from backend.application.enums.supported_platform import SupportedPlatform
from backend.domain.enums.output_language import OutputLanguage


class GenerationRequest(BaseModel):
    url: HttpUrl
    platform: SupportedPlatform
    access_token: str | None = None
    iteration: int
    output_language: OutputLanguage


class GenerationResponse(BaseModel):
    documentation_id: str

class DuplicateRepositoryError(BaseModel):
    detail: str
    existing_documentation_id: str