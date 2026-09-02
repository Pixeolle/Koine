import asyncio
import json

from collections.abc import AsyncIterable

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from backend.application.ports.document_repository import DocumentRepository
from backend.application.ports.progress_reporter import ProgressEventType
from backend.core.dependencies.document import build_document_repository
from backend.domain.entities.documentation import DocumentationStatus
from backend.infrastructure.api.dependencies import get_progress_broker
from backend.domain.services.progress_broker import ProgressBroker

progress_router = APIRouter()

@progress_router.get('/{documentation_id}/progress')
async def get_documentation_progress(
        documentation_id: str,
        progress_broker: ProgressBroker = Depends(get_progress_broker),
        document_repository: DocumentRepository = Depends(build_document_repository)
) -> StreamingResponse:

    try:
        documentation = document_repository.get_documentation(documentation_id)
    except Exception as _:
        documentation = None

    if documentation is not None and documentation.status is DocumentationStatus.FINISHED:
        async def stream_documentation_finished() -> AsyncIterable[str]:
            yield _serialize_event({
                "type": ProgressEventType.COMPLETE
            })
            return

        return StreamingResponse(stream_documentation_finished(), media_type="text/event-stream")

    if not progress_broker.is_available(documentation_id):
        raise HTTPException(status_code=404, detail="No generation found for this id")

    history, queue = progress_broker.subscribe(documentation_id)

    async def progress_event_stream() -> AsyncIterable[str]:
        try:
            for event in history:
                yield _serialize_event(event)

            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    yield ": heartbeat\n\n"
                    continue

                yield _serialize_event(event)

                if event["type"] in (ProgressEventType.COMPLETE, ProgressEventType.ERROR):
                    break

        except Exception as e:
            logger.exception(f"SSE crashed, {e}")
            raise
        finally:
            progress_broker.unsubscribe(documentation_id, queue)

        return

    return StreamingResponse(progress_event_stream(), media_type="text/event-stream")

def _serialize_event(event: dict) -> str:
    event = event.copy()
    event_type: ProgressEventType = event.pop("type")
    return f"data: {json.dumps({"type": event_type.value, **event})}\n\n"