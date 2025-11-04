"""
Chat API endpoints for Deep Agent AGI.

Provides REST endpoints for chat conversations with the deep agent,
including standard request/response and streaming via SSE.
"""
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from deep_agent.core.logging import get_logger
from deep_agent.core.serialization import serialize_event
from deep_agent.models.chat import ChatRequest, ChatResponse, Message, MessageRole, ResponseStatus
from deep_agent.services.agent_service import AgentService

logger = get_logger(__name__)

# Create API router
router = APIRouter()

# Initialize rate limiter for chat endpoints
limiter = Limiter(key_func=get_remote_address)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # 10 chat requests per minute per IP
async def chat(
    request_body: ChatRequest,
    request: Request,
) -> ChatResponse:
    """
    Send a message to the deep agent and receive a complete response.

    This endpoint provides synchronous request/response chat interaction.
    For streaming responses, use POST /chat/stream instead.

    Args:
        request_body: Chat request containing message and thread_id
        request: FastAPI request object (for request_id access)

    Returns:
        ChatResponse with agent's reply and conversation state

    Raises:
        HTTPException: 500 if agent execution fails

    Example:
        ```python
        # Request
        POST /api/v1/chat
        {
            "message": "What files are in my project?",
            "thread_id": "user-123",
            "metadata": {"source": "web"}
        }

        # Response
        {
            "messages": [
                {"role": "user", "content": "What files are in my project?", "timestamp": "..."},
                {"role": "assistant", "content": "I found 15 files...", "timestamp": "..."}
            ],
            "thread_id": "user-123",
            "status": "success",
            "metadata": {"tokens": 250, "model": "gpt-5"}
        }
        ```
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "Chat request received",
        request_id=request_id,
        thread_id=request_body.thread_id,
        message_length=len(request_body.message),
        has_metadata=request_body.metadata is not None,
    )

    try:
        # Initialize agent service
        service = AgentService()

        # Invoke agent
        result = await service.invoke(
            message=request_body.message,
            thread_id=request_body.thread_id,
        )

        # Extract messages from result
        messages_data = result.get("messages", [])

        # Convert to Message objects
        messages = [
            Message(
                role=MessageRole(msg.get("role", "assistant")),
                content=msg.get("content", ""),
            )
            for msg in messages_data
        ]

        logger.info(
            "Chat request completed successfully",
            request_id=request_id,
            thread_id=request_body.thread_id,
            message_count=len(messages),
        )

        # Build response
        return ChatResponse(
            messages=messages,
            thread_id=request_body.thread_id,
            status=ResponseStatus.SUCCESS,
            metadata=request_body.metadata,
        )

    except ValueError as e:
        # Validation errors from AgentService
        logger.warning(
            "Chat request validation error",
            request_id=request_id,
            thread_id=request_body.thread_id,
            error=str(e),
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    except Exception as e:
        # Agent execution errors
        # Sanitize error message before logging (security)
        from deep_agent.core.security import sanitize_error_message

        error_msg = sanitize_error_message(str(e))

        logger.error(
            "Chat request failed",
            request_id=request_id,
            thread_id=request_body.thread_id,
            error=error_msg,  # Sanitized error message
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed",
        )


@router.post("/chat/stream")
@limiter.limit("10/minute")  # Same rate limit as standard chat
async def chat_stream(
    request_body: ChatRequest,
    request: Request,
) -> StreamingResponse:
    """
    Stream agent response events via Server-Sent Events (SSE).

    This endpoint provides real-time streaming of agent execution events,
    allowing clients to display progress, tool calls, and partial responses
    as they occur. Uses the SSE protocol for browser compatibility.

    NOTE: Error Handling Difference from /chat endpoint:
    - Validation errors (422): Raised as HTTPException before streaming starts
    - Runtime errors: Sent as SSE error events within the stream (not HTTPException)
    This allows clients to handle errors within their SSE event handlers.

    Args:
        request_body: Chat request containing message and thread_id
        request: FastAPI request object (for request_id access)

    Returns:
        StreamingResponse with text/event-stream content type

    Raises:
        HTTPException: 422 if validation fails before streaming starts

    SSE Event Format:
        ```
        data: {"event_type": "on_chat_model_stream", "data": {...}, "timestamp": "..."}

        data: {"event_type": "on_tool_start", "data": {...}, "timestamp": "..."}

        ```

    Example:
        ```javascript
        // Client-side JavaScript
        const eventSource = new EventSource('/api/v1/chat/stream', {
            method: 'POST',
            body: JSON.stringify({
                message: "What files are in my project?",
                thread_id: "user-123"
            })
        });

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Event:', data.event_type, data.data);
        };
        ```
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        "Chat stream request received",
        request_id=request_id,
        thread_id=request_body.thread_id,
        message_length=len(request_body.message),
        has_metadata=request_body.metadata is not None,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        """
        Generate SSE-formatted events from agent stream.

        Yields SSE data lines in the format: "data: {json}\n\n"
        """
        try:
            # Initialize agent service
            service = AgentService()

            # Stream events from agent
            async for event in service.stream(
                message=request_body.message,
                thread_id=request_body.thread_id,
            ):
                # Serialize event to JSON-safe format (handles LangChain/LangGraph objects)
                serialized_event = serialize_event(event)

                # Format event as SSE
                # SSE format: "data: {json}\n\n"
                event_json = json.dumps(serialized_event)
                yield f"data: {event_json}\n\n"

            logger.info(
                "Chat stream completed successfully",
                request_id=request_id,
                thread_id=request_body.thread_id,
            )

        except GeneratorExit:
            # Client disconnected - clean up gracefully
            logger.info(
                "Chat stream client disconnected",
                request_id=request_id,
                thread_id=request_body.thread_id,
            )
            # No need to yield error - connection already closed
            raise  # Re-raise to properly close the generator

        except ValueError as e:
            # Validation errors from AgentService
            logger.warning(
                "Chat stream validation error",
                request_id=request_id,
                thread_id=request_body.thread_id,
                error=str(e),
            )

            # Send error as SSE event
            error_event = {
                "event_type": "error",
                "data": {"error": str(e), "status": "validation_error"},
            }
            yield f"data: {json.dumps(error_event)}\n\n"

        except Exception as e:
            # Agent execution errors
            # Sanitize error message before logging (security)
            from deep_agent.core.security import sanitize_error_message

            error_msg = sanitize_error_message(str(e))

            logger.error(
                "Chat stream failed",
                request_id=request_id,
                thread_id=request_body.thread_id,
                error=error_msg,  # Sanitized error message
                error_type=type(e).__name__,
            )

            # Send error as SSE event
            error_event = {
                "event_type": "error",
                "data": {"error": "Agent execution failed", "status": "error"},
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    # Return streaming response with SSE content type
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Request-ID": request_id,
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
