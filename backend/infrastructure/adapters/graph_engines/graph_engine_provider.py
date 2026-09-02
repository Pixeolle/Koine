from backend.application.ports.graph_engine import GraphEngine
from backend.infrastructure.adapters.graph_engines.neo4j.neo4j_adapter import Neo4jAdapter
from backend.infrastructure.adapters.graph_engines.rustworkx_adapter import RustworkxAdapter


class GraphEngineProvider:

    @staticmethod
    def get_graph_engine(*, neo4j_host: str | None = None, neo4j_port: int | None = None) -> GraphEngine:

        is_neo4j_available = neo4j_host is not None and neo4j_port is not None
        if is_neo4j_available:
            assert neo4j_host is not None
            assert neo4j_port is not None
            return Neo4jAdapter(host=neo4j_host, port=neo4j_port)

        return RustworkxAdapter()
