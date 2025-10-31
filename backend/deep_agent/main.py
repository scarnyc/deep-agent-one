"""
FastAPI application entry point for Deep Agent AGI.

Provides HTTP API with CORS, rate limiting, structured logging,
and global exception handling.
"""
import json
import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

from deep_agent.api.dependencies import AgentServiceDep
from deep_agent.api.middleware import TimeoutMiddleware
from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.errors import ConfigurationError, DeepAgentError
from deep_agent.core.logging import LogLevel, generate_langsmith_url, get_logger, setup_logging
from deep_agent.core.serialization import serialize_event

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


class WebSocketMessage(BaseModel):
    """
    WebSocket message model for client requests.

    Attributes:
        type: Message type (e.g., "chat")
        message: User message content
        thread_id: Conversation thread identifier
        metadata: Optional metadata
    """

    type: str = Field(
        description="Message type (e.g., 'chat')",
    )
    message: str = Field(
        min_length=1,
        description="User message content",
    )
    thread_id: str = Field(
        min_length=1,
        description="Conversation thread identifier",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata",
    )

    @field_validator("message", "thread_id", mode="before")
    @classmethod
    def strip_and_validate_string(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        if not isinstance(v, str):
            raise ValueError("Value must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Value cannot be empty or whitespace-only")

        return stripped


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

    # Initialize logging with appropriate format and level
    log_level = LogLevel.DEBUG if settings.DEBUG else LogLevel.INFO
    log_format = "standard" if settings.DEBUG else "json"
    setup_logging(log_level=log_level, log_format=log_format)

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
        allowed_origins = settings.cors_origins_list

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

    # Add request timeout middleware
    app.add_middleware(TimeoutMiddleware, timeout=30)
    logger.debug("Request timeout middleware enabled", timeout_seconds=30)

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

    # WebSocket endpoint for AG-UI Protocol
    @app.websocket("/api/v1/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        service: AgentServiceDep,
    ) -> None:
        """
        WebSocket endpoint for real-time agent communication.

        Provides bidirectional communication channel for streaming agent
        responses. Clients send chat messages and receive streaming events
        following the AG-UI Protocol.

        Protocol:
            Client → Server:
                {
                    "type": "chat",
                    "message": "User message here",
                    "thread_id": "unique-thread-id",
                    "metadata": {"user_id": "123"}  // optional
                }

            Server → Client (Events):
                {
                    "event": "on_chat_model_stream",
                    "data": {"chunk": {"content": "..."}},
                    "request_id": "uuid"
                }

            Server → Client (Errors):
                {
                    "type": "error",
                    "error": "Error message",
                    "request_id": "uuid"
                }

        Example:
            ```javascript
            const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

            ws.onopen = () => {
                ws.send(JSON.stringify({
                    type: 'chat',
                    message: 'Hello, agent!',
                    thread_id: 'user-123'
                }));
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Event:', data);
            };
            ```

        Args:
            websocket: FastAPI WebSocket connection
            service: AgentService dependency (injected)

        Raises:
            WebSocketDisconnect: When client disconnects
        """
        # Accept WebSocket connection
        await websocket.accept()

        # Generate connection ID for logging
        connection_id = str(uuid.uuid4())

        logger.info(
            "WebSocket connection established",
            connection_id=connection_id,
        )

        # NOTE: We don't send a connection_established event here because:
        # 1. AG-UI Protocol doesn't define such an event
        # 2. WebSocket.accept() is sufficient - frontend knows connection is ready
        # 3. Sending non-standard events can cause frontend handler errors
        # Connection state is managed by the WebSocket lifecycle itself.

        try:
            while True:
                # Receive message from client
                try:
                    raw_data = await websocket.receive_text()
                    data = json.loads(raw_data)
                except json.JSONDecodeError as e:
                    # Invalid JSON
                    logger.warning(
                        "WebSocket received invalid JSON",
                        connection_id=connection_id,
                        error=str(e),
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid JSON format",
                    })
                    continue

                # Generate request ID for this message
                request_id = str(uuid.uuid4())

                logger.info(
                    "WebSocket message received",
                    connection_id=connection_id,
                    request_id=request_id,
                    message_type=data.get("type"),
                )

                # Validate message structure
                try:
                    message = WebSocketMessage(**data)
                except ValidationError as e:
                    # Validation error
                    logger.warning(
                        "WebSocket message validation failed",
                        connection_id=connection_id,
                        request_id=request_id,
                        errors=e.errors(),
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Validation error: {str(e)}",
                        "request_id": request_id,
                    })
                    continue

                # Process chat message
                if message.type == "chat":
                    try:
                        logger.info(
                            "Starting WebSocket streaming",
                            connection_id=connection_id,
                            request_id=request_id,
                            thread_id=message.thread_id,
                            message_preview=message.message[:50] if len(message.message) > 50 else message.message,
                        )

                        # CUSTOM EVENT: processing_started
                        # This is NOT part of AG-UI Protocol - it's a custom event for UX feedback
                        # during cold starts (8-10s). Frontend must filter this event before passing
                        # to AG-UI handler to prevent "unknown event" errors.
                        await websocket.send_json({
                            "event": "processing_started",
                            "data": {
                                "message": "Agent initializing...",
                                "request_id": request_id,
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        })

                        event_count = 0
                        trace_id = None
                        # Stream agent responses using injected service
                        async for event in service.stream(
                            message=message.message,
                            thread_id=message.thread_id,
                        ):
                            event_count += 1

                            # Capture trace_id from first event metadata if available
                            if trace_id is None and "metadata" in event:
                                trace_id = event["metadata"].get("trace_id")

                            # Add request_id to event for tracking
                            event["request_id"] = request_id

                            # Serialize event to JSON-safe format (handles LangChain objects)
                            serialized_event = serialize_event(event)

                            # Send event to client
                            await websocket.send_json(serialized_event)

                            # Log progress every 10 events
                            if event_count % 10 == 0:
                                logger.debug(
                                    f"WebSocket sent {event_count} events",
                                    connection_id=connection_id,
                                    request_id=request_id,
                                    trace_id=trace_id,
                                )

                        logger.info(
                            "WebSocket message processing completed",
                            connection_id=connection_id,
                            request_id=request_id,
                            thread_id=message.thread_id,
                            trace_id=trace_id,
                            total_events_sent=event_count,
                        )

                    except ValueError as e:
                        # Validation errors from AgentService
                        logger.warning(
                            "WebSocket agent validation error",
                            connection_id=connection_id,
                            request_id=request_id,
                            thread_id=message.thread_id,
                            error=str(e),
                        )
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e),
                            "request_id": request_id,
                            "thread_id": message.thread_id,
                        })

                    except asyncio.CancelledError:
                        # Client disconnected or task cancelled
                        # Get trace_id if available
                        captured_trace_id = trace_id if 'trace_id' in locals() else None
                        captured_event_count = event_count if 'event_count' in locals() else 0

                        logger.info(
                            "WebSocket streaming cancelled (client disconnect or timeout)",
                            connection_id=connection_id,
                            request_id=request_id,
                            thread_id=message.thread_id,
                            trace_id=captured_trace_id,
                            events_sent=captured_event_count,
                            reason="client_disconnect_or_task_cancelled",
                        )
                        # Do NOT send error to client (connection likely closed)
                        # Do NOT re-raise (expected behavior)
                        # Continue to next message in the while loop

                    except Exception as e:
                        # Agent execution errors
                        # Sanitize error message (security)
                        error_msg = str(e)
                        if any(pattern in error_msg for pattern in ["sk-", "lsv2_", "key=", "token=", "password="]):
                            error_msg = "[REDACTED: Potential secret in error message]"

                        # Get trace_id if available
                        captured_trace_id = trace_id if 'trace_id' in locals() else None

                        logger.error(
                            "WebSocket agent execution failed",
                            connection_id=connection_id,
                            request_id=request_id,
                            thread_id=message.thread_id,
                            trace_id=captured_trace_id,
                            langsmith_url=generate_langsmith_url(captured_trace_id) if captured_trace_id else None,
                            error=error_msg,
                            error_type=type(e).__name__,
                        )
                        await websocket.send_json({
                            "type": "error",
                            "error": "Agent execution failed",
                            "request_id": request_id,
                            "thread_id": message.thread_id,
                            "trace_id": captured_trace_id,
                        })

                else:
                    # Unknown message type
                    logger.warning(
                        "WebSocket unknown message type",
                        connection_id=connection_id,
                        request_id=request_id,
                        message_type=message.type,
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {message.type}",
                        "request_id": request_id,
                    })

        except WebSocketDisconnect:
            logger.info(
                "WebSocket client disconnected",
                connection_id=connection_id,
            )

        except Exception as e:
            logger.error(
                "WebSocket unexpected error",
                connection_id=connection_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            try:
                await websocket.close()
            except (WebSocketDisconnect, RuntimeError):
                pass  # Connection may already be closed

    # Include API routers
    from deep_agent.api.v1 import agents, chat

    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(agents.router, prefix="/api/v1", tags=["agents"])

    logger.info("FastAPI app created successfully")

    return app


# Create app instance for uvicorn
app = create_app()
