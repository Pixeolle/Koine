import re

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class SourceCode(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    source_code: bytes

    @property
    def get_extension(self) -> str:
        EXTRACT_EXTENSION_REGEX = r'[.].*$'

        match = re.search(EXTRACT_EXTENSION_REGEX, str(self.path))
        if match is None:
            return ''

        return match.group(0)
