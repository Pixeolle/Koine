from pathlib import Path

from pydantic import BaseModel, PrivateAttr, computed_field


class DirectorySettings(BaseModel):
    fileignore_filename: Path
    outputs_dir: str
    temporary_dir: str

    _root_path: Path = PrivateAttr(default=Path(__file__).resolve().parent.parent.parent.parent)

    @computed_field
    @property
    def fileignore_filepath(self) -> Path:
        return self._root_path / self.fileignore_filename

    @computed_field
    @property
    def outputs_path(self) -> Path:
        src_path = Path(__file__).resolve().parent.parent.parent
        return  src_path.parent / self.outputs_dir

    @computed_field
    @property
    def temporary_path(self) -> Path:
        return self.outputs_path / self.temporary_dir
