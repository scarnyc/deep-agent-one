"""
WebSocket endpoint for Deep Agent AGI (AG-UI Protocol).

Provides WebSocket-based bidirectional communication for real-time
agent interaction with AG-UI event streaming.
"""
import json
import uuid
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError, field_validator

from backend.deep_agent.core.logging import get_logger
from backend.deep_agent.services.agent_service import AgentService

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
    metadata: Dict[str, Any] | None = Field(
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
async def websocket_endpoint(websocket: WebSocket) -> None:
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
                    # Initialize agent service
                    service = AgentService()

                    # Stream agent responses
                    async for event in service.stream(
                        message=message.message,
                        thread_id=message.thread_id,
                    ):
                        # Add request_id to event for tracking
                        event["request_id"] = request_id

                        # Send event to client
                        await websocket.send_json(event)

                    logger.info(
                        "WebSocket message processing completed",
                        connection_id=connection_id,
                        request_id=request_id,
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
        except:
            pass  # Connection may already be closed
