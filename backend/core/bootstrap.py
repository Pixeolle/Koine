import sys

from loguru import logger

from backend.core.settings import settings


def boostrap_system() -> None:
    _set_up_directories()
    _set_up_logger()

def _set_up_directories() -> None:
    settings.directory.outputs_path.mkdir(parents=True, exist_ok=True)
    settings.directory.temporary_path.mkdir(parents=True, exist_ok=True)

def _set_up_logger() -> None:
   logger.remove()
   logger.add(sys.stderr, level=settings.logger.level.value)
