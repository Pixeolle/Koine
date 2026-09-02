from pathlib import Path

from backend.application.ports.llm_tokenizer import LLMTokenizer
from backend.domain.entities.code_node import CodeNode
from backend.domain.entities.llm_enrichment_input import (
    CallContext,
    Child,
    LLMEnrichmentInput,
)
from backend.domain.entities.llm_message import LLMMessage, LLMMessageRole
from backend.domain.enums.output_language import OutputLanguage


class PromptFactory:

    def __init__(
            self,
            output_language: OutputLanguage,
            llm_tokenizer: LLMTokenizer,
            max_context_tokens: int,
            system_enrichment_prompt: str
    ):
        self.output_language = output_language
        self._llm_tokenizer = llm_tokenizer
        self._max_token_length = max_context_tokens

        self._system_enrichment_prompt = system_enrichment_prompt

    @classmethod
    def from_prompt_paths(
            cls,
            output_language: OutputLanguage,
            llm_tokenizer: LLMTokenizer,
            max_context_tokens: int,
            system_enrichment_prompt_filepath: Path
    ):
        system_enrichment_prompt = system_enrichment_prompt_filepath.read_text('utf8').strip()

        return cls(
            output_language=output_language,
            llm_tokenizer=llm_tokenizer,
            max_context_tokens=max_context_tokens,
            system_enrichment_prompt = system_enrichment_prompt
        )

    def build_enrichment_prompt(
            self,
            node: CodeNode,
            children: list[Child],
            call_contexts: list[CallContext]
    ) -> list[LLMMessage]:
        return [
            LLMMessage(
                role=LLMMessageRole.SYSTEM,
                content=self._system_enrichment_prompt
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content=_build_enrichment_input(node, children, call_contexts).model_dump_json()
            )
        ]


def _build_enrichment_input(
        node: CodeNode,
        children: list[Child],
        call_contexts: list[CallContext]
) -> LLMEnrichmentInput:
    return LLMEnrichmentInput(
        fqn=node.code_block.fqn,
        node_type=node.code_block.type,
        raw_code=node.code_block.source_code,
        call_contexts=call_contexts,
        children=children
    )
