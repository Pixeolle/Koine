from pathlib import Path
from typing import Self

from pydantic import BaseModel, HttpUrl, PrivateAttr, computed_field, model_validator

from backend.domain.enums.llm_provider_type import LLMProviderType
from backend.domain.enums.output_language import OutputLanguage


class LLMClientSettings(BaseModel):
    name: str
    provider: LLMProviderType
    model: str
    base_url: HttpUrl
    api_key: str
    temperature: float
    tokenizer_filename: Path
    hf_repo: str | None
    max_context_tokens: int
    concurrency_limit: int

    _tokenizer_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent.parent / 'tokenizers')

    @computed_field
    @property
    def tokenizer_filepath(self) -> Path:
        return self._tokenizer_path / self.tokenizer_filename

    @model_validator(mode='after')
    def validate_provider_dependencies(self) -> Self:
        match self.provider:
            case LLMProviderType.LOCAL_MISTRAL:
                if self.hf_repo is None and self._tokenizer_path is None:
                    raise ValueError("hf_repo and tokenizer_filename can't be both null")

        return self


class LLMPromptSettings(BaseModel):
    output_language: OutputLanguage
    enrichment_system_prompt_filename: Path
    min_messages_tokens: int
    max_messages_tokens: int

    _prompts_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent / 'prompts')

    @computed_field
    @property
    def system_enrichment_prompt_filepath(self) -> Path:
        return self._prompts_path / self.enrichment_system_prompt_filename


class LLMSettings(BaseModel):
    client: LLMClientSettings
    prompt: LLMPromptSettings

    @model_validator(mode='after')
    def validate_cross_coherence(self) -> Self :
        if self.client.max_context_tokens < self.prompt.max_messages_tokens:
            raise ValueError(
                'La taille maximale des feuilles regroupés dépasse la taille maximal du model'
            )

        return self
