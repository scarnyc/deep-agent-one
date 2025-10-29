"""
WebSocket endpoint for Deep Agent AGI (AG-UI Protocol).

Provides WebSocket-based bidirectional communication for real-time
agent interaction with AG-UI event streaming.
"""
import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from pydantic import BaseModel, Field, ValidationError, field_validator

from deep_agent.api.dependencies import AgentServiceDep
from deep_agent.core.logging import get_logger
from deep_agent.core.serialization import serialize_event

logger = get_logger(__name__)

# Create API router
router = APIRouter()


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


@router.websocket("/ws")
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
                    # Stream agent responses using injected service
                    async for event in service.stream(
                        message=message.message,
                        thread_id=message.thread_id,
                    ):
                        event_count += 1

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
                            )

                    logger.info(
                        "WebSocket message processing completed",
                        connection_id=connection_id,
                        request_id=request_id,
                        total_events_sent=event_count,
                    )

                except ValueError as e:
                    # Validation errors from AgentService
                    logger.warning(
                        "WebSocket agent validation error",
                        connection_id=connection_id,
                        request_id=request_id,
                        error=str(e),
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "request_id": request_id,
                    })

                except Exception as e:
                    # Agent execution errors
                    # Sanitize error message (security)
                    error_msg = str(e)
                    if any(pattern in error_msg for pattern in ["sk-", "lsv2_", "key=", "token=", "password="]):
                        error_msg = "[REDACTED: Potential secret in error message]"

                    logger.error(
                        "WebSocket agent execution failed",
                        connection_id=connection_id,
                        request_id=request_id,
                        error=error_msg,
                        error_type=type(e).__name__,
                    )
                    await websocket.send_json({
                        "type": "error",
                        "error": "Agent execution failed",
                        "request_id": request_id,
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
