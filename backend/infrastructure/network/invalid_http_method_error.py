
class InvalidHTTPMethodError(ValueError):
    def __init__(self, method: str):
        message = f'Methode HTTP non supporté ({method})'
        super().__init__(message)
