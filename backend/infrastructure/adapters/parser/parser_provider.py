from backend.application.ports.parser import Parser
from backend.domain.enums.supported_language import SupportedLanguage
from backend.infrastructure.adapters.parser.default_parser import DefaultParser
from backend.infrastructure.adapters.parser.tree_sitter_parser import TreeSitterParser


class ParserProvider:

    @staticmethod
    def from_language(language: SupportedLanguage) -> Parser:
        match language:
            case SupportedLanguage.PYTHON:
                return TreeSitterParser(language)
            case SupportedLanguage.DEFAULT:
                return DefaultParser()
