import httpx

from backend.core.settings import settings
from backend.domain.exceptions.repository_access_denied import RepositoryAccessDenied
from backend.domain.exceptions.repository_network_error import RepositoryNetworkError
from backend.domain.exceptions.repository_not_found import RepositoryNotFound
from backend.infrastructure.network.http_response import HTTPResponse
from backend.infrastructure.network.invalid_http_method_error import InvalidHTTPMethodError
from backend.infrastructure.network.type_request import TypeRequest


class HTTPClient:
    def __init__(self):
      self.http_client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self.http_client = httpx.AsyncClient(
            headers={
                'User-Agent': 'Koine/1.0',
                'Accept': '*/*',
                'Connection': 'close'
            },
            timeout=httpx.Timeout(
                connect=settings.httpx.connect_timeout,
                read=settings.httpx.read_timeout,
                write=60.0,
                pool=60.0
            ),
            http2=False,
            limits=httpx.Limits(
                max_connections=5,
                max_keepalive_connections=5,
                keepalive_expiry=2.0
            ),
            trust_env=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            await self.http_client.aclose()

    async def request(self, type_request: TypeRequest, url: str, headers: dict[str, str] | None) -> HTTPResponse:
        if not self.http_client:
            raise RuntimeError('Utiliser le client http dans un bloc with')

        try:
            response = await self._send_request(type_request, url, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            status = error.response.status_code

            if status in (401, 403):
                raise RepositoryAccessDenied(url) from error

            if status == 404:
                raise RepositoryNotFound(url) from error

            raise RepositoryNetworkError(url, f"Error HTTP {status}") from error

        except httpx.RequestError as error:
            raise RepositoryNetworkError(url, str(error)) from error

        return HTTPResponse(
            status_code=response.status_code,
            headers=response.headers,
            content=response.content
        )

    async def _send_request(self, type_request: TypeRequest, url: str, headers: dict[str, str] | None) -> httpx.Response:
        assert self.http_client is not None

        match type_request:
            case TypeRequest.GET:
                return await self.http_client.get(url, headers=headers)
            case TypeRequest.HEAD:
                return await self.http_client.head(url, headers=headers)

        raise InvalidHTTPMethodError(type_request)
