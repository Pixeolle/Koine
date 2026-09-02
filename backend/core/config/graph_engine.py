from pydantic import BaseModel


class GraphEngineSettings(BaseModel):
    neo4j_host: str | None = None
    neo4j_port: int | None = None
