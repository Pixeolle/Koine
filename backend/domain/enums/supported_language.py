from enum import Enum


class SupportedLanguage(Enum):
    PYTHON = [".py"]
    DEFAULT = []

    def __init__(self, extensions: list[str]):
        self.extensions = extensions

    @classmethod
    def extension_available(cls) -> list[str]:
        return [
            extension
            for supported_language in SupportedLanguage
            if supported_language is not SupportedLanguage.DEFAULT
            for extension in supported_language.extensions
        ]
