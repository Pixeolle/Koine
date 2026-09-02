from pydantic import BaseModel

from backend.domain.enums.output_language import OutputLanguage
from backend.application.enums.supported_platform import SupportedPlatform


class OutputLanguageResponse(BaseModel):
    code: str
    label: str

    @classmethod
    def from_domain(cls, output_language: OutputLanguage) -> "OutputLanguageResponse":
        return cls(
            code=output_language.code,
            label=output_language.label
        )

class SupportedPlatformResponse(BaseModel):
    id: str
    label: str

    @classmethod
    def from_domain(cls, supported_platform: SupportedPlatform) -> "SupportedPlatformResponse":
        return cls(
            id=supported_platform.name,
            label=supported_platform.value
        )