"""
Logging Middleware.

Adds request ID and logging context to API requests.
"""

from collections.abc import Callable
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging_factory import bind_context, clear_context, get_logger


logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add logging context to requests.

    Automatically generates and binds request IDs for distributed tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging context.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from handler
        """
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Bind context for this request
        bind_context(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        # Log request
        logger.info(
            "api_request_received",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
        )

        try:
            # Process request
            response = await call_next(request)

            # Log response
            logger.info(
                "api_request_completed", status_code=response.status_code, success=True,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            logger.error(
                "api_request_failed",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise

        finally:
            # Clear context after request
            clear_context()
