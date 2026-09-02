from backend.application.enums.supported_platform import SupportedPlatform
from backend.domain.exceptions.domain_error import DomainError


class UnsupportedPlatformError(DomainError):
    def __init__(self, url: str):
        self.url = url
        supported_platform_str = ', '.join([supported_platform.platform_name for supported_platform in SupportedPlatform])
        self.message = (f"La plateforme n'est pas supporté pour l'url:{url} \n"
                        f"Plateforme supportés: {supported_platform_str}")
        super().__init__(self.message)
