"""
Chat API endpoints for Deep Agent AGI.

Provides REST endpoints for chat conversations with the deep agent,
including standard request/response and streaming via SSE.
"""
from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.deep_agent.core.logging import get_logger
from backend.deep_agent.models.chat import ChatRequest, ChatResponse, Message, MessageRole, ResponseStatus
from backend.deep_agent.services.agent_service import AgentService

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
        error_msg = str(e)

        # Check if error might contain sensitive data (API keys, tokens)
        # Common patterns: sk- (OpenAI), lsv2_ (LangSmith), etc.
        if any(pattern in error_msg for pattern in ["sk-", "lsv2_", "key=", "token=", "password="]):
            error_msg = "[REDACTED: Potential secret in error message]"

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
