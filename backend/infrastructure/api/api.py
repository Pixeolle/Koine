from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.dependencies.llm import build_llm_client
from backend.core.dependencies.api import build_progress_broker
from backend.infrastructure.api.documentations.router import documentations_router
from backend.infrastructure.api.generations.router import generations_router
from backend.infrastructure.api.metadata.router import metadata_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.llm_client = build_llm_client()
    app.state.progress_broker = build_progress_broker()

    yield

api = FastAPI(
    title="Koine",
    description="Generate documentation from repository",
    lifespan=lifespan
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],
    allow_methods=["*"],
    allow_headers=["*"]
)

api.include_router(documentations_router, prefix="/api/documentations")
api.include_router(generations_router, prefix="/api/generate")
api.include_router(metadata_router, prefix='/api/metadata')

@api.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
