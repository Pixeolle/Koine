from pathlib import Path
from typing import Self

from pydantic import BaseModel, PrivateAttr, computed_field, model_validator


class WriterSettings(BaseModel):
    system_prompt_filename: Path
    starting_prompt_filename: Path
    starting_block_creation_filename: Path
    starting_block_revision_filename: Path

    _prompts_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent / 'prompts')

    @computed_field
    def system_prompt_filepath(self) -> Path:
        return self._prompts_path / self.system_prompt_filename

    @computed_field
    def starting_prompt_filepath(self) -> Path:
        return self._prompts_path / self.starting_prompt_filename

    @computed_field
    def starting_block_creation_filepath(self) -> Path:
        return self._prompts_path / self.starting_block_creation_filename

    @computed_field
    def starting_block_revision_filepath(self) -> Path:
        return self._prompts_path / self.starting_block_revision_filename

class StructurerSettings(BaseModel):
    system_prompt_filename: Path
    starting_prompt_filename: Path

    _prompts_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent / 'prompts')

    @computed_field
    def system_prompt_filepath(self) -> Path:
        return self._prompts_path / self.system_prompt_filename

    @computed_field
    def starting_prompt_filepath(self) -> Path:
        return self._prompts_path / self.starting_prompt_filename

class JudgeSettings(BaseModel):
    system_prompt_filename: Path
    starting_prompt_filename: Path

    _prompts_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent / 'prompts')

    @computed_field
    def system_prompt_filepath(self) -> Path:
        return self._prompts_path / self.system_prompt_filename

    @computed_field
    def starting_prompt_filepath(self) -> Path:
        return self._prompts_path / self.starting_prompt_filename

class AssistantSettings(BaseModel):
    system_prompt_filename: Path
    starting_prompt_filename: Path

    _prompts_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent / 'prompts')

    @computed_field
    def system_prompt_filepath(self) -> Path:
        return self._prompts_path / self.system_prompt_filename

    @computed_field
    def starting_prompt_filepath(self) -> Path:
        return self._prompts_path / self.starting_prompt_filename

class AgentSettings(BaseModel):
    max_context_token_length: int
    max_context_token_length_after_compression: int
    start_percentile_compression: int
    end_percentile_compression: int
    compression_system_prompt_filename: Path

    structurer: StructurerSettings
    writer: WriterSettings
    judge: JudgeSettings
    assistant: AssistantSettings

    _prompts_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent / 'prompts')

    @computed_field
    def compression_system_prompt_filepath(self) -> Path:
        return self._prompts_path / self.compression_system_prompt_filename

    @model_validator(mode='after')
    def percentile_valid(self) -> Self:
        is_start_percentile_valide = 0 <=self.start_percentile_compression <= 100
        is_end_percentile_valide = 0 <= self.end_percentile_compression <=100
        if not is_start_percentile_valide or not is_end_percentile_valide:
            raise ValueError("Percentile cannot be under 0 or exceed 100")

        return self
