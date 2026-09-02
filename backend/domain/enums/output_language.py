from enum import Enum


class OutputLanguage(Enum):
    FRENCH = ('fr', "Français")
    ENGLISH = ('en', "English")

    def __new__(cls, code: str, label: str):
        obj = object.__new__(cls)
        obj._value_ = code
        obj.code = code
        obj.label = label
        return obj

    @property
    def text(self):
        return self.name.lower()
