"""
Chat API endpoints for Deep Agent AGI.

Provides REST endpoints for chat conversations with the deep agent,
including standard request/response and streaming via SSE.
"""

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from deep_agent.core.errors import safe_validation_error
from deep_agent.core.logging import get_logger
from deep_agent.core.security import sanitize_error_with_metadata
from deep_agent.core.serialization import serialize_event
from deep_agent.models.chat import ChatRequest, ChatResponse, Message, MessageRole, ResponseStatus
from deep_agent.services.agent_service import AgentService

# Pre-defined static error responses for SSE streaming (CWE-209: prevent info exposure)
# These are disconnected from any exception data to prevent stack trace leakage
_SSE_ERROR_VALIDATION: str = json.dumps(
    {
        "event_type": "error",
        "data": {"error": "Validation failed", "status": "validation_error"},
    }
)
_SSE_ERROR_EXECUTION: str = json.dumps(
    {
        "event_type": "error",
        "data": {"error": "Agent execution failed", "status": "error"},
    }
)

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

        # Convert LangChain message objects to Message objects
        messages = []
        for msg in messages_data:
            # Handle LangChain message objects (have .type and .content attributes)
            if hasattr(msg, "type") and hasattr(msg, "content"):
                # Skip messages with empty content (e.g., Gemini thinking/reasoning output)
                if not msg.content or not msg.content.strip():
                    logger.debug(
                        "Skipping message with empty content",
                        message_type=msg.type,
                    )
                    continue

                # Map LangChain message types to API MessageRole
                role_map = {"ai": "assistant", "human": "user", "system": "system"}
                role = role_map.get(msg.type, "assistant")
                messages.append(
                    Message(
                        role=MessageRole(role),
                        content=msg.content,
                    )
                )
            # Fallback for dictionary format (for backward compatibility)
            elif isinstance(msg, dict):
                content = msg.get("content", "")
                # Skip messages with empty content
                if not content or not content.strip():
                    logger.debug(
                        "Skipping dict message with empty content",
                        message_role=msg.get("role", "unknown"),
                    )
                    continue

                messages.append(
                    Message(
                        role=MessageRole(msg.get("role", "assistant")),
                        content=content,
                    )
                )
            else:
                # Unknown format, convert to string
                str_content = str(msg)
                # Skip if conversion results in empty string
                if not str_content.strip():
                    continue

                messages.append(
                    Message(
                        role=MessageRole("assistant"),
                        content=str_content,
                    )
                )

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
        # Sanitize error message with metadata for enhanced logging
        sanitization = sanitize_error_with_metadata(str(e), e)

        logger.warning(
            "Chat request validation error",
            request_id=request_id,
            thread_id=request_body.thread_id,
            error=sanitization.message,
            sanitized=sanitization.was_sanitized,
            original_error_type=sanitization.original_error_type,
        )

        # Return safe error to client (CWE-209: prevent info exposure)
        # Uses whitelist to provide actionable errors when safe
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=safe_validation_error(str(e)),
        ) from e

    except Exception as e:
        # Agent execution errors
        # Sanitize error message with metadata for enhanced logging
        sanitization = sanitize_error_with_metadata(str(e), e)

        logger.error(
            "Chat request failed",
            request_id=request_id,
            thread_id=request_body.thread_id,
            error=sanitization.message,
            sanitized=sanitization.was_sanitized,
            original_error_type=sanitization.original_error_type,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed",
        ) from e


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

        except ValueError:
            # Validation errors from AgentService
            # Log exception details server-side only (CWE-209: prevent info exposure)
            # NOTE: We intentionally don't access exception data for the response
            # to prevent any data flow from exception to client response
            logger.warning(
                "Chat stream validation error",
                request_id=request_id,
                thread_id=request_body.thread_id,
            )

            # Yield pre-defined static error (no connection to exception data)
            yield f"data: {_SSE_ERROR_VALIDATION}\n\n"

        except Exception:
            # Agent execution errors
            # Log exception details server-side only (CWE-209: prevent info exposure)
            # NOTE: We intentionally don't access exception data for the response
            # to prevent any data flow from exception to client response
            logger.exception(
                "Chat stream failed",
                request_id=request_id,
                thread_id=request_body.thread_id,
            )

            # Yield pre-defined static error (no connection to exception data)
            yield f"data: {_SSE_ERROR_EXECUTION}\n\n"

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
