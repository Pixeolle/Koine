from pathlib import Path

from backend.domain.exceptions.domain_error import DomainError


class FileSystemError(DomainError):
    def __init__(self, path: str | Path, details: str):
        message = f"Impossible d'écrire ou lire le fichier {path} \nDetails: {details}"
        super().__init__(message)
