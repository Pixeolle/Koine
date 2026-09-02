from dataclasses import dataclass

from backend.application.ports.llm_client import LLMClient
from backend.application.ports.llm_tokenizer import LLMTokenizer


@dataclass
class BaseAgentParameters:
    llm_client: LLMClient
    llm_tokenizer: LLMTokenizer
    max_context_token_length: int
    max_context_token_length_after_compression: int
    start_percentile_compression: int
    end_percentile_compression: int
    compression_system_prompt: str
