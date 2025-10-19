"""
FastAPI application entry point for Deep Agent AGI.

Provides HTTP API with CORS, rate limiting, structured logging,
and global exception handling.
"""
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

from backend.deep_agent.config.settings import Settings, get_settings
from backend.deep_agent.core.errors import ConfigurationError, DeepAgentError
from backend.deep_agent.core.logging import get_logger

logger = get_logger(__name__)


def get_limiter_key(request: Request) -> str:
    """
    Get rate limiting key from request.

    Uses client IP address from X-Forwarded-For header (if behind proxy)
    or remote address directly. In production with authentication,
    can be extended to use user ID for more precise rate limiting.

    Args:
        request: FastAPI request object

    Returns:
        Key string for rate limiting (IP address or user identifier)
    """
    settings = get_settings()

    # If in production/staging, trust X-Forwarded-For header from reverse proxy
    if settings.ENV in ["staging", "prod"]:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can be "client, proxy1, proxy2"
            # Take the first (leftmost) IP as the actual client
            client_ip = forwarded_for.split(",")[0].strip()
            return client_ip

    # Fallback to direct remote address (local/dev environments)
    return get_remote_address(request)


# Initialize rate limiter
limiter = Limiter(key_func=get_limiter_key)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the FastAPI app.

    Args:
        app: FastAPI application instance

    Yields:
        None during application runtime
    """
    # Startup
    settings = get_settings()
    logger.info(
        "Starting Deep Agent AGI API",
        env=settings.ENV,
        debug=settings.DEBUG,
        api_version=settings.API_VERSION,
    )

    yield

    # Shutdown
    logger.info("Shutting down Deep Agent AGI API")


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create and configure FastAPI application.

    Args:
        settings: Configuration settings. If None, uses get_settings().

    Returns:
        Configured FastAPI application instance
    """
    if settings is None:
        settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title="Deep Agent AGI",
        description="General-purpose deep agent framework with cost optimization",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,  # Disable docs in prod
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Add CORS middleware
    if settings.CORS_ORIGINS:
        allowed_origins = [
            origin.strip() for origin in settings.CORS_ORIGINS.split(",")
        ]

        # Security: Validate CORS configuration
        if "*" in allowed_origins:
            raise ConfigurationError(
                "CORS misconfiguration: Cannot use allow_credentials=True with "
                "wildcard origins ('*'). This would allow any website to make "
                "authenticated requests to your API. Use specific origins instead."
            )

        # Production safety check
        if settings.ENV == "prod" and any("localhost" in origin for origin in allowed_origins):
            logger.warning(
                "Production CORS configuration includes localhost origins",
                allowed_origins=allowed_origins,
            )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        logger.debug("CORS enabled", allowed_origins=allowed_origins)

    # Add rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    logger.debug(
        "Rate limiting enabled",
        requests=settings.RATE_LIMIT_REQUESTS,
        period_seconds=settings.RATE_LIMIT_PERIOD,
    )

    # Add structured logging middleware
    @app.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Log all HTTP requests with structured data."""
        request_id = str(uuid.uuid4())

        # Add request_id to request state for access in handlers
        request.state.request_id = request_id

        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=get_remote_address(request),
        )

        # Process request
        response = await call_next(request)

        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "Request completed",
            request_id=request_id,
            status_code=response.status_code,
        )

        return response

    # Global exception handlers
    @app.exception_handler(DeepAgentError)
    async def deep_agent_error_handler(
        request: Request,
        exc: DeepAgentError,
    ) -> JSONResponse:
        """Handle custom DeepAgent errors."""
        logger.error(
            "DeepAgent error",
            request_id=getattr(request.state, "request_id", None),
            error=str(exc),
            error_type=type(exc).__name__,
            context=exc.context,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": exc.message,
                "error_type": type(exc).__name__,
                "context": exc.context,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        # Convert errors to JSON-serializable format
        errors = []
        for error in exc.errors():
            # Extract the error dict and convert non-serializable values
            error_dict = {
                "type": error["type"],
                "loc": error["loc"],
                "msg": error["msg"],
                "input": error.get("input"),
            }

            # Handle ctx (context) which may contain ValueError objects
            if "ctx" in error:
                ctx = error["ctx"]
                if isinstance(ctx, dict):
                    # Convert ValueError/Exception objects to strings
                    error_dict["ctx"] = {
                        k: str(v) if isinstance(v, Exception) else v for k, v in ctx.items()
                    }

            errors.append(error_dict)

        logger.warning(
            "Validation error",
            request_id=getattr(request.state, "request_id", None),
            errors=errors,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected errors."""
        logger.error(
            "Unexpected error",
            request_id=getattr(request.state, "request_id", None),
            error=str(exc),
            error_type=type(exc).__name__,
        )

        # Don't expose internal error details in production
        if settings.DEBUG:
            detail = str(exc)
            error_type = type(exc).__name__
        else:
            detail = "Internal server error"
            error_type = "InternalServerError"  # Generic type in production

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": detail,
                "error_type": error_type,  # Only specific type in debug mode
            },
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """
        Health check endpoint.

        Returns:
            Status dict indicating service health
        """
        return {"status": "healthy"}

    # Include API routers
    from backend.deep_agent.api.v1 import chat

    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

    # TODO: Include remaining routers when implemented
    # from backend.deep_agent.api.v1 import agents, websocket
    # app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
    # app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])

    logger.info("FastAPI app created successfully")

    return app


# Create app instance for uvicorn
app = create_app()
