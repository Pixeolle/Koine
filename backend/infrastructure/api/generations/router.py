import asyncio
from collections.abc import Awaitable, Callable
from uuid import uuid4

from loguru import logger
from fastapi import APIRouter, Depends, Form, HTTPException

from backend.application.ports.document_repository import DocumentRepository
from backend.application.mappers.create_repository_url import CreateRepositoryURL
from backend.application.use_cases.run_documentation_pipeline_use_case import RunDocumentationPipelineUseCase
from backend.core.dependencies.api import build_progress_reporter
from backend.core.dependencies.document import build_document_repository
from backend.core.dependencies.ingest import build_check_repository_available
from backend.domain.services.progress_broker import ProgressBroker
from backend.domain.entities.repository_status import RepositoryStatus
from backend.domain.entities.repository_url import RepositoryURL
from backend.infrastructure.api.dependencies import (
    get_run_documentation_pipeline_use_case,
    get_progress_broker,
)
from backend.infrastructure.api.generations.schemas import DuplicateRepositoryError, GenerationRequest, GenerationResponse
from backend.infrastructure.api.generations.progress.router import progress_router

generations_router = APIRouter()
generations_router.include_router(progress_router)

_running_task: set[asyncio.Task] = set()

@generations_router.post("")
async def generate_documentation(
        request: GenerationRequest,
        run_documentation_pipeline_use_case: RunDocumentationPipelineUseCase = Depends(get_run_documentation_pipeline_use_case),
        broker: ProgressBroker = Depends(get_progress_broker),
        check_repository_available: Callable[[RepositoryURL], Awaitable[RepositoryStatus]] = Depends(build_check_repository_available),
        document_repository: DocumentRepository = Depends(build_document_repository)
) -> GenerationResponse:
    documentation_id = str(uuid4())
    repository_url = CreateRepositoryURL.from_generation_request(request)
    repository_status = await check_repository_available(repository_url)

    if not repository_status.is_available:
        raise HTTPException(status_code=401, detail="You don't have the right to access to this repository" )

    assert repository_status.content_filename is not None
    previous_documentation = document_repository.get_documentation_by_hash(repository_status.content_filename)
    if previous_documentation is not None:
        raise HTTPException(status_code=409, detail=DuplicateRepositoryError(
            detail="This repository state has already been documented",
            existing_documentation_id=previous_documentation.documentation_id
        ))

    broker.start(documentation_id)
    progress_reporter = build_progress_reporter(documentation_id, broker)

    try:
        documentation_task = asyncio.create_task(
            run_documentation_pipeline_use_case.run(
                end_reporting=lambda: broker.close(documentation_id),
                documentation_id=documentation_id,
                repository_url=repository_url,
                output_language=request.output_language,
                max_documentation_iteration=request.iteration,
                progress_reporter=progress_reporter
            )
        )
        _running_task.add(documentation_task)
        documentation_task.add_done_callback(_running_task.discard)

    except Exception as error:
        logger.error(error)
        raise

    return GenerationResponse(documentation_id=documentation_id)

