from enum import Enum


class SupportedPlatform(Enum):
    GITLAB = 'GitLab'
    GITHUB = 'GitHub'

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
