"""
Rate limiting middleware for SSE connections.

This module provides rate limiting for SSE connections to prevent abuse
and ensure fair resource allocation.
"""

from collections import defaultdict
from collections.abc import Callable
import time

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings


class SSERateLimiter(BaseHTTPMiddleware):
    """
    Rate limit SSE connections per user session.

    Tracks:
    - Active concurrent connections per session
    - Connection duration
    - Connection start times

    Limits:
    - Maximum concurrent connections (default: 3)
    - Maximum connection duration (default: 3600 seconds)
    """

    def __init__(
        self, app, max_concurrent: int | None = None, max_duration: int | None = None,
    ):
        """
        Initialize SSE rate limiter.

        Args:
            app: FastAPI application
            max_concurrent: Maximum concurrent connections per session
            max_duration: Maximum connection duration in seconds
        """
        super().__init__(app)
        self.max_concurrent = max_concurrent or settings.SSE_MAX_CONCURRENT_CONNECTIONS
        self.max_duration = max_duration or settings.SSE_CONNECTION_TIMEOUT

        # Track active connections per session
        # Format: {session_id: [start_time1, start_time2, ...]}
        self.active_connections: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting for SSE endpoints.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from next handler or rate limit error
        """
        # Only apply to SSE proxy endpoints
        if not request.url.path.startswith("/sse-proxy/"):
            return await call_next(request)

        # Get session ID
        session_id = request.session.get("api_key_id")
        if not session_id:
            # Not authenticated, let auth middleware handle it
            return await call_next(request)

        # Clean up expired connections
        current_time = time.time()
        if session_id in self.active_connections:
            self.active_connections[session_id] = [
                start_time
                for start_time in self.active_connections[session_id]
                if current_time - start_time < self.max_duration
            ]

        # Check concurrent connection limit
        active_count = len(self.active_connections.get(session_id, []))
        if active_count >= self.max_concurrent:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many concurrent SSE connections",
                    "detail": f"Maximum {self.max_concurrent} concurrent connections allowed",
                    "active_connections": active_count,
                },
            )

        # Track this connection
        connection_start = current_time
        self.active_connections[session_id].append(connection_start)

        try:
            # Process request
            return await call_next(request)

        finally:
            # Remove connection when done
            if session_id in self.active_connections:
                try:
                    self.active_connections[session_id].remove(connection_start)

                    # Clean up empty entries
                    if not self.active_connections[session_id]:
                        del self.active_connections[session_id]
                except ValueError:
                    # Connection already removed, ignore
                    pass

    def get_active_connections(self, session_id: str) -> int:
        """
        Get number of active connections for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(session_id, []))

    def get_total_connections(self) -> int:
        """
        Get total number of active connections across all sessions.

        Returns:
            Total active connection count
        """
        return sum(len(conns) for conns in self.active_connections.values())
