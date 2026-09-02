

class DomainError(Exception):
    def __init__(self, message: str | None = None):
        if message is None:
            message = "Une erreur domaine s'est produite"
        super().__init__(message)
