from backend.domain.exceptions.domain_error import DomainError


class RepositoryNetworkError(DomainError):
    def __init__(self, url: str, details: str):
        message = f"Impossible de joindre {url}. \nDetails: {details}"
        super().__init__(message)
