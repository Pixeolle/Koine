from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.core.config.agent import AgentSettings
from backend.core.config.directory import DirectorySettings
from backend.core.config.document_repository import DocumentRepositorySettings
from backend.core.config.graph_engine import GraphEngineSettings
from backend.core.config.httpx import HTTPXSettings
from backend.core.config.llm import LLMSettings
from backend.core.config.logger import LoggerSettings
from backend.core.config.server import ServerSettings

DOTENV_PATH = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    server: ServerSettings
    httpx: HTTPXSettings
    directory: DirectorySettings
    llm: LLMSettings
    logger: LoggerSettings
    graph_engine: GraphEngineSettings
    document_repository: DocumentRepositorySettings
    agent: AgentSettings

    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH / ".env",
        env_file_encoding="utf8",
        env_nested_delimiter='__',
        extra="ignore"
    )


settings = Settings()
