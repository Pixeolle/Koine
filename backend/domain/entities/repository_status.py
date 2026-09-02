from dataclasses import dataclass


@dataclass
class RepositoryStatus:
    is_available: bool
    content_filename: str | None = None