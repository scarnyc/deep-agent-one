"""Custom middleware for FastAPI application."""

import asyncio
from typing import Callable

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from deep_agent.core.logging import get_logger

logger = get_logger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeout limits.

    Prevents requests from running indefinitely, protecting against
    DoS attacks and resource exhaustion.
    """

    def __init__(self, app, timeout: int = 30):
        """
        Initialize timeout middleware.

        Args:
            app: FastAPI application instance
            timeout: Maximum request duration in seconds (default: 30)
        """
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with timeout protection.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in the chain

        Returns:
            Response from handler or timeout error
        """
        try:
            # Execute request with timeout
            async with asyncio.timeout(self.timeout):
                response = await call_next(request)
                return response

        except TimeoutError:
            logger.warning(
                "Request timeout",
                path=request.url.path,
                method=request.method,
                timeout=self.timeout,
            )
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Request timeout",
                    "detail": f"Request exceeded {self.timeout}s timeout limit",
                },
            )
