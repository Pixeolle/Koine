from backend.domain.exceptions.domain_error import DomainError


class RepositoryAccessDenied(DomainError):
    def __init__(self, url: str) -> None:
        message = f"Access Denied: {url}"
        super().__init__(message)
