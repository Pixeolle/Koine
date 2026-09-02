import re

from urllib.parse import quote, urlparse

from backend.domain.entities.repository_informations import RepositoryInformations
from backend.domain.entities.repository_url import GitLabURL
from backend.infrastructure.adapters.repository_fetcher.base_git_adapter import BaseGitAdapter


class GitLabAPIAdapter(BaseGitAdapter):

    @staticmethod
    def _build_api_url(repository_url: GitLabURL) -> str:
        parsed_url = urlparse(repository_url.url)

        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        request_body = str(parsed_url.path.strip('/'))
        project_path = re.sub(r"/-/tree/.*", "", request_body)
        branch_match = re.search(r"/-/tree/(.*)", request_body)
        encoded_path = quote(project_path, safe="")

        is_branch_found = branch_match is not None and branch_match[1] is not None
        params = f"?sha={branch_match[1]}" if is_branch_found else ""

        return f"{base_url}/api/v4/projects/{encoded_path}/repository/archive.zip{params}"

    @staticmethod
    def extract_repository_informations(repository_url: GitLabURL) -> RepositoryInformations:
        repository_branch = GitLabAPIAdapter._extract_branch(repository_url.url)
        repository_name = GitLabAPIAdapter._extract_name(repository_url.url, repository_branch is not None)
        return RepositoryInformations(
            name=repository_name,
            branch=repository_branch
        )

    @staticmethod
    def _extract_name(url: str, has_branch: bool) -> str:
        REGEX_EXTRACT_NAME = {
            True: r".*/(.*)/-/tree",
            False: r"/([^/]*)$"
        }

        match = re.search(REGEX_EXTRACT_NAME[has_branch], url)
        name = None if match is None else match[1]

        if name is None:
            raise ValueError(f"URL invalid, {url} doesn't contain any repository name")
        assert isinstance(name, str)
        return name

    @staticmethod
    def _extract_branch(url: str) -> str | None:
        match = re.search(r"/-/tree/([^?]*)?", url)
        if match is None:
            return None
        return match[1]


