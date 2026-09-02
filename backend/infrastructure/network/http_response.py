from pydantic import BaseModel, ConfigDict


class HTTPResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    status_code: int
    headers: dict
    content: bytes
