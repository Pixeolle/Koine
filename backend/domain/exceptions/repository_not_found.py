from backend.domain.exceptions.domain_error import DomainError


class RepositoryNotFound(DomainError):
    def __init__(self, url: str):
        message = f"Le repository est introuvable: {url}"
        super().__init__(message)
