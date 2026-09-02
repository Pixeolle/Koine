from loguru import logger

from backend.application.ports.graph_engine import GraphEngine
from backend.core.settings import settings
from backend.infrastructure.adapters.graph_engines.graph_engine_provider import GraphEngineProvider


def build_graph_engine() -> GraphEngine:
    logger.info(f"Connect to Graph Engine at {settings.graph_engine.neo4j_host}:{settings.graph_engine.neo4j_port}")
    return GraphEngineProvider.get_graph_engine(
        neo4j_host=settings.graph_engine.neo4j_host,
        neo4j_port=settings.graph_engine.neo4j_port
    )
