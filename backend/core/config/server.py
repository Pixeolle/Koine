from pydantic import BaseModel


class ServerSettings(BaseModel):
    host: str
    port: int
