from fastapi import FastAPI

from backend.application.ports.progress_reporter import ProgressReporter
from backend.domain.services.progress_broker import ProgressBroker
from backend.infrastructure.api.generations.progress.queue_progress_reporter import QueueProgressReporter


def create_api() -> FastAPI:
    from backend.infrastructure.api.api import api
    return api

def build_progress_broker() -> ProgressBroker:
    return ProgressBroker()

def build_progress_reporter(documentation_id: str, progress_broker: ProgressBroker) -> ProgressReporter:
    return QueueProgressReporter(
        documentation_id,
        progress_broker
    )

