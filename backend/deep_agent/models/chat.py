"""
Chat API Pydantic models for request/response validation.

This module provides models for:
- Chat messages with roles and timestamps (Message, MessageRole)
- Chat API request/response structure (ChatRequest, ChatResponse)
- Streaming event models for real-time updates (StreamEvent)
- Response status tracking (ResponseStatus)

Models:
    MessageRole: Enum for message sender roles (user, assistant, system)
    ResponseStatus: Enum for response outcomes (success, error, pending)
    Message: Single message with role, content, and timestamp
    ChatRequest: User message with thread_id and optional metadata
    ChatResponse: Agent response with messages list, status, and debugging identifiers
    StreamEvent: Server-Sent Event (SSE) for streaming agent execution

Validation Features:
    - Non-empty string validation with whitespace stripping
    - Auto-generated UTC timestamps for messages and events
    - Metadata size/depth validation (max 10KB, 5 levels) for DoS prevention
    - JSON-serializable metadata enforcement

Security Notes:
    - ChatRequest.metadata is validated for size (10KB max) and depth (5 levels max)
      to prevent DoS attacks via large payloads or RecursionError from deep nesting
    - All strings are stripped and validated to prevent empty/whitespace-only inputs

Example:
    >>> from deep_agent.models.chat import ChatRequest, ChatResponse, Message, MessageRole, ResponseStatus
    >>> # Create request
    >>> request = ChatRequest(
    ...     message="What files are in my project?",
    ...     thread_id="user-123",
    ...     metadata={"source": "web"}
    ... )
    >>> # Create response
    >>> msg = Message(role=MessageRole.ASSISTANT, content="Here are your files...")
    >>> response = ChatResponse(
    ...     messages=[msg],
    ...     thread_id="user-123",
    ...     status=ResponseStatus.SUCCESS,
    ...     trace_id="trace-abc-456"
    ... )

Streaming Example:
    >>> from deep_agent.models.chat import StreamEvent
    >>> event = StreamEvent(
    ...     event_type="on_chat_model_stream",
    ...     data={"content": "Hello"},
    ...     thread_id="user-123"
    ... )
    >>> # Serialize to SSE format
    >>> print(f"event: {event.event_type}\\ndata: {event.data}\\n\\n")
"""
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    """
    Message role types for chat conversations.

    Defines who generated a message in the conversation.
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ResponseStatus(str, Enum):
    """
    Response status types for chat responses.

    Indicates the outcome of an agent invocation.
    """

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class Message(BaseModel):
    """
    A single message in a chat conversation.

    Attributes:
        role: The role of the message sender (user, assistant, system)
        content: The text content of the message
        timestamp: When the message was created (auto-generated if not provided)

    Example:
        >>> msg = Message(role=MessageRole.USER, content="Hello")
        >>> print(msg.role, msg.content)
        MessageRole.USER Hello
    """

    role: MessageRole = Field(
        description="The role of the message sender",
    )
    content: str = Field(
        min_length=1,
        description="The text content of the message",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the message was created (UTC)",
    )

    @field_validator("content", mode="before")
    @classmethod
    def strip_and_validate_content(cls, v: Any) -> str:
        """Strip whitespace and validate content is not empty."""
        if not isinstance(v, str):
            raise ValueError("Content must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Content cannot be empty or whitespace-only")

        return stripped

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "user",
                "content": "What is the weather today?",
                "timestamp": "2025-01-01T12:00:00",
            }
        }
    }


class ChatRequest(BaseModel):
    """
    Request model for chat endpoints.

    Attributes:
        message: The user's message to send to the agent
        thread_id: Unique identifier for the conversation thread
        metadata: Optional metadata about the request (e.g., user_id, source)

    Example:
        >>> req = ChatRequest(message="Hello", thread_id="user-123")
        >>> print(req.message, req.thread_id)
        Hello user-123
    """

    message: str = Field(
        min_length=1,
        description="The user's message to send to the agent",
    )
    thread_id: str = Field(
        min_length=1,
        description="Unique identifier for the conversation thread",
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the request",
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

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata_size_and_depth(cls, v: Any) -> dict[str, Any] | None:
        """
        Validate metadata dict is not too large or deeply nested.

        Security constraints:
        - Maximum serialized size: 10KB (prevents DoS via large payloads)
        - Maximum nesting depth: 5 levels (prevents RecursionError)

        Args:
            v: Metadata value to validate

        Returns:
            Validated metadata dict or None if no metadata provided

        Raises:
            ValueError: If metadata exceeds size/depth limits
        """
        if v is None:
            return None

        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")

        # Validate serialization size (prevents huge payloads)
        try:
            serialized = json.dumps(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Metadata must be JSON-serializable: {e}") from e

        max_size_bytes = 10000  # 10KB limit
        if len(serialized) > max_size_bytes:
            raise ValueError(
                f"Metadata payload too large ({len(serialized)} bytes, max {max_size_bytes} bytes)"
            )

        # Validate nesting depth (prevents RecursionError)
        def check_depth(obj: Any, current_depth: int = 0, max_depth: int = 5) -> None:
            """Recursively check nesting depth of dict/list structures."""
            if current_depth > max_depth:
                raise ValueError(f"Metadata nesting too deep (max {max_depth} levels)")

            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, current_depth + 1, max_depth)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1, max_depth)

        check_depth(v)
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What files are in my project?",
                "thread_id": "user-456",
                "metadata": {"source": "web", "user_id": "12345"},
            }
        }
    }


class ChatResponse(BaseModel):
    """
    Response model for chat endpoints.

    Attributes:
        messages: List of messages in the conversation (must be non-empty)
        thread_id: Unique identifier for the conversation thread
        status: Status of the response (success, error, pending)
        metadata: Optional metadata about the response (e.g., tokens, model)
        error: Optional error message if status is ERROR

    Example:
        >>> from deep_agent.models.chat import Message, MessageRole, ResponseStatus
        >>> msg = Message(role=MessageRole.ASSISTANT, content="Hello")
        >>> resp = ChatResponse(
        ...     messages=[msg],
        ...     thread_id="user-123",
        ...     status=ResponseStatus.SUCCESS
        ... )
        >>> print(resp.status, len(resp.messages))
        ResponseStatus.SUCCESS 1
    """

    messages: list[Message] = Field(
        min_length=1,
        description="List of messages in the conversation",
    )
    thread_id: str = Field(
        min_length=1,
        description="Unique identifier for the conversation thread",
    )
    status: ResponseStatus = Field(
        description="Status of the response",
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the response",
    )
    error: Optional[str] = Field(
        default=None,
        description="Optional error message if status is ERROR",
    )
    trace_id: Optional[str] = Field(
        default=None,
        description="LangSmith trace ID for debugging (links to execution trace)",
    )
    run_id: Optional[str] = Field(
        default=None,
        description="LangGraph checkpoint/run ID for state inspection",
    )

    @field_validator("thread_id", mode="before")
    @classmethod
    def strip_and_validate_thread_id(cls, v: Any) -> str:
        """Strip whitespace and validate thread_id is not empty."""
        if not isinstance(v, str):
            raise ValueError("Thread ID must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Thread ID cannot be empty or whitespace-only")

        return stripped

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {"role": "user", "content": "Hello", "timestamp": "2025-01-01T12:00:00"},
                    {"role": "assistant", "content": "Hi there!", "timestamp": "2025-01-01T12:00:01"},
                ],
                "thread_id": "user-123",
                "status": "success",
                "metadata": {"tokens": 100, "model": "gpt-5"},
            }
        }
    }


class StreamEvent(BaseModel):
    """
    Event model for streaming agent responses.

    Used for Server-Sent Events (SSE) to stream agent execution in real-time.

    Attributes:
        event_type: Type of event (e.g., "on_chat_model_stream", "on_tool_start")
        data: Event payload data (structure varies by event type)
        timestamp: When the event was created (auto-generated if not provided)
        thread_id: Optional thread identifier for the conversation

    Example:
        >>> event = StreamEvent(
        ...     event_type="on_chat_model_stream",
        ...     data={"content": "Hello"},
        ...     thread_id="user-123"
        ... )
        >>> print(event.event_type, event.data)
        on_chat_model_stream {'content': 'Hello'}
    """

    event_type: str = Field(
        min_length=1,
        description="Type of event",
    )
    data: dict[str, Any] = Field(
        description="Event payload data",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the event was created (UTC)",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional thread identifier for the conversation",
    )

    @field_validator("event_type", mode="before")
    @classmethod
    def strip_and_validate_event_type(cls, v: Any) -> str:
        """Strip whitespace and validate event_type is not empty."""
        if not isinstance(v, str):
            raise ValueError("Event type must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Event type cannot be empty or whitespace-only")

        return stripped

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_type": "on_chat_model_stream",
                "data": {"content": "Hello, how can I help you today?"},
                "timestamp": "2025-01-01T12:00:00",
                "thread_id": "user-123",
            }
        }
    }
