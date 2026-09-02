from fastapi import APIRouter, Depends, HTTPException

from backend.application.ports.graph_engine import GraphEngine
from backend.application.ports.document_repository import DocumentRepository
from backend.core.dependencies.document import build_document_repository
from backend.infrastructure.api.documentations.document.router import documents_router
from backend.infrastructure.api.documentations.chat.router import chat_router
from backend.infrastructure.api.documentations.schemas import DocumentationSummary
from backend.core.dependencies.graph import build_graph_engine
from backend.domain.services.progress_broker import ProgressBroker
from backend.infrastructure.api.dependencies import get_progress_broker
from backend.infrastructure.api.documentations.schemas import DocumentSummary


documentations_router = APIRouter()

documentations_router.include_router(documents_router, prefix="/{documentation_id}/document")
documentations_router.include_router(chat_router, prefix="/{documentation_id}/chat")


@documentations_router.get("")
async def list_documentations(
        document_repository: DocumentRepository = Depends(build_document_repository)
) -> list[DocumentationSummary]:
    return [
        DocumentationSummary.from_domain(documentation)
        for documentation in document_repository.get_documentations()
    ]

@documentations_router.delete("/{documentation_id}", status_code=204)
async def delete_documentation(
        documentation_id: str,
        document_repository: DocumentRepository = Depends(build_document_repository),
        graph_engine: GraphEngine = Depends(build_graph_engine),
        broker: ProgressBroker = Depends(get_progress_broker)
) -> None:
    if broker.is_available(documentation_id):
        raise HTTPException(status_code=409, detail="Generation still in progress for this documentation.")
    if not document_repository.get_documentation(documentation_id):
        raise HTTPException(status_code=404, detail="Documentation not found.")

    document_repository.delete_documentation(documentation_id)
    graph_engine.delete_graph(documentation_id)
    return

@documentations_router.get("/{documentation_id}/documents")
async def list_documents(
        documentation_id: str,
        document_repository: DocumentRepository = Depends(build_document_repository)
) -> list[DocumentSummary]:
    return [
        DocumentSummary.from_domain(document)
        for document in document_repository.get_documents(documentation_id)
    ]


