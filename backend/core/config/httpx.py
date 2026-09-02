from pydantic import BaseModel


class HTTPXSettings(BaseModel):
    connect_timeout: float = 10.0
    read_timeout: float = 240.0
    keep_alive_timeout: float = 10.0
