from backend.application.ports.document_repository import DocumentRepository
from backend.core.settings import settings
from backend.infrastructure.adapters.document_repositories.localfs_sqlite_adapter import LocalFSSqLiteAdapter


def build_document_repository() -> DocumentRepository:
    return LocalFSSqLiteAdapter(
        database_path=settings.document_repository.sqlite_filepath,
        documentation_repository_path=settings.document_repository.sqlite_path
    )
