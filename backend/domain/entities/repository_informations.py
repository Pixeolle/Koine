from pydantic import BaseModel


class RepositoryInformations(BaseModel):
    name: str
    branch: str | None
