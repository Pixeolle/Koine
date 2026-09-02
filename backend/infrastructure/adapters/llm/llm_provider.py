import httpx

from backend.application.ports.llm_client import LLMClient
from backend.application.ports.llm_tokenizer import LLMTokenizer
from backend.core.config.llm import LLMClientSettings
from backend.domain.enums.llm_provider_type import LLMProviderType
from backend.infrastructure.adapters.llm.client.openai_client import OpenAIClient
from backend.infrastructure.adapters.llm.tokenizer.mistral_tokenizer import MistralTokenizer


class LLMProvider:

    @staticmethod
    def get_llm(llm_settings: LLMClientSettings) -> tuple[LLMClient, LLMTokenizer]:
        match llm_settings.provider:
            case LLMProviderType.LOCAL_MISTRAL:
                assert llm_settings.hf_repo is not None

                http_client = httpx.AsyncClient(verify=False)
                llm_client = OpenAIClient(
                    model=llm_settings.model,
                    base_url=str(llm_settings.base_url),
                    api_key=llm_settings.api_key,
                    http_client=http_client
                )

                llm_tokenizer = MistralTokenizer(
                    hg_repo=llm_settings.hf_repo,
                    file_path=llm_settings.tokenizer_filepath
                )

                return llm_client, llm_tokenizer
