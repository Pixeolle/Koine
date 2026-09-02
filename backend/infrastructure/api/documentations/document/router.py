from fastapi import APIRouter, Depends

from backend.application.ports.document_repository import DocumentRepository
from backend.core.dependencies.document import build_document_repository
from backend.infrastructure.api.documentations.schemas import DocumentResponse

documents_router = APIRouter()

@documents_router.get("/{document_name:path}")
async def get_document(
        documentation_id: str,
        document_name: str,
        document_repository: DocumentRepository = Depends(build_document_repository)
) -> DocumentResponse | None:
    try:
        document = document_repository.get_document(documentation_id, document_name)
    except Exception as _:
        return None

    return DocumentResponse.from_domain(document)
