from fastapi import APIRouter, Depends, Form, HTTPException

from backend.application.enums.supported_platform import SupportedPlatform
from backend.domain.enums.output_language import OutputLanguage
from backend.infrastructure.api.metadata.schemas import OutputLanguageResponse, SupportedPlatformResponse

metadata_router = APIRouter()

@metadata_router.get("/output_languages")
async def get_output_languages() -> list[OutputLanguageResponse]:
    return [
        OutputLanguageResponse.from_domain(output_language)
        for output_language in OutputLanguage
    ]

@metadata_router.get("/supported_platforms")
async def get_supported_platforms() -> list[SupportedPlatformResponse]:
    return [
        SupportedPlatformResponse.from_domain(supported_platform)
        for supported_platform in SupportedPlatform
    ]
