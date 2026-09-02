import uvicorn

from backend.core.settings import settings


def start_server():
    uvicorn.run(
        'backend.core.dependencies.api:create_api',
        host=settings.server.host,
        port=settings.server.port,
    )
