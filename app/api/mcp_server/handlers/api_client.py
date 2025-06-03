"""API client for communicating with the Trading API."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Generic, Optional, Type, TypeVar
from urllib.parse import urljoin

import httpx
import structlog
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import config

T = TypeVar("T", bound=BaseModel)

logger = structlog.get_logger()


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class APIConnectionError(APIError):
    """Raised when unable to connect to the API."""

    pass


class APITimeoutError(APIError):
    """Raised when API request times out."""

    pass


class APIValidationError(APIError):
    """Raised when API returns validation errors."""

    pass


class APIClient:
    """HTTP client for communicating with the Trading API."""

    def __init__(self):
        """Initialize the API client."""
        self.base_url = config.api_base_url.rstrip("/")
        self.timeout = httpx.Timeout(
            connect=config.request_timeout,
            read=config.request_timeout,
            write=config.request_timeout,
            pool=config.request_timeout,
        )
        self.headers = {
            "User-Agent": f"Trading-MCP-Server/{config.server_version}",
            "Accept": "application/json",
        }
        if config.api_key:
            self.headers["Authorization"] = f"Bearer {config.api_key}"

        # Configure connection pool
        self.limits = httpx.Limits(
            max_keepalive_connections=config.connection_pool_size,
            max_connections=config.connection_pool_size * 2,
            keepalive_expiry=30,  # seconds
        )

        self._client: Optional[httpx.AsyncClient] = None
        self.logger = logger.bind(component="api_client")

    @asynccontextmanager
    async def _get_client(self):
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self.headers,
                limits=self.limits,
                follow_redirects=True,
            )
        try:
            yield self._client
        except Exception:
            # Don't close on error, keep connection pool
            raise

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for an endpoint."""
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return endpoint

    @retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic."""
        url = self._build_url(endpoint)

        log = self.logger.bind(
            method=method, url=url, params=params, has_json=json_data is not None
        )

        log.info("Making API request")

        try:
            async with self._get_client() as client:
                response = await client.request(
                    method=method, url=url, params=params, json=json_data, **kwargs
                )

                try:
                    elapsed_ms = response.elapsed.total_seconds() * 1000
                except RuntimeError:
                    elapsed_ms = None

                log.info(
                    "API request completed",
                    status_code=response.status_code,
                    elapsed_ms=elapsed_ms,
                )

                response.raise_for_status()
                return response

        except httpx.ConnectError as e:
            log.error("Connection error", error=str(e))
            raise APIConnectionError(f"Failed to connect to API: {e}")
        except httpx.TimeoutException as e:
            log.error("Request timeout", error=str(e))
            raise APITimeoutError(f"API request timed out: {e}")
        except httpx.HTTPStatusError as e:
            log.error("HTTP error", status_code=e.response.status_code, error=str(e))
            self._handle_http_error(e.response)
        except Exception as e:
            log.error("Unexpected error", error=str(e), error_type=type(e).__name__)
            raise

    def _handle_http_error(self, response: httpx.Response):
        """Handle HTTP error responses."""
        try:
            error_data = response.json()
            message = error_data.get("detail", response.text)
        except Exception:
            message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 400:
            raise APIValidationError(
                message,
                response.status_code,
                error_data if "error_data" in locals() else None,
            )
        elif response.status_code == 401:
            raise APIError("Authentication failed", response.status_code)
        elif response.status_code == 403:
            raise APIError("Permission denied", response.status_code)
        elif response.status_code == 404:
            raise APIError("Resource not found", response.status_code)
        elif response.status_code >= 500:
            raise APIError(f"Server error: {message}", response.status_code)
        else:
            raise APIError(message, response.status_code)

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make a GET request."""
        response = await self._make_request("GET", endpoint, params=params, **kwargs)
        return response.json()

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make a POST request."""
        response = await self._make_request(
            "POST", endpoint, params=params, json_data=json, **kwargs
        )
        return response.json()

    async def get_typed(
        self,
        endpoint: str,
        response_model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> T:
        """Make a GET request and parse response with Pydantic model."""
        data = await self.get(endpoint, params=params, **kwargs)
        return response_model(**data)

    async def post_typed(
        self,
        endpoint: str,
        response_model: Type[T],
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> T:
        """Make a POST request and parse response with Pydantic model."""
        data = await self.post(endpoint, json_data=json_data, params=params, **kwargs)
        return response_model(**data)

    async def stream_get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ):
        """Make a GET request and stream the response."""
        url = self._build_url(endpoint)

        async with self._get_client() as client:
            async with client.stream("GET", url, params=params, **kwargs) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    yield chunk

    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            # Assuming the API has a health endpoint
            await self.get("/health")
            return True
        except Exception as e:
            self.logger.warning("Health check failed", error=str(e))
            return False


# Global client instance
_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get the global API client instance."""
    global _client
    if _client is None:
        _client = APIClient()
    return _client


async def cleanup_api_client():
    """Clean up the global API client."""
    global _client
    if _client:
        await _client.close()
        _client = None
