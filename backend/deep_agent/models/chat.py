"""Chat API Pydantic models for request/response validation."""
from datetime import datetime
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
        default_factory=datetime.utcnow,
        description="When the message was created",
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
        >>> from backend.deep_agent.models.chat import Message, MessageRole, ResponseStatus
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
        default_factory=datetime.utcnow,
        description="When the event was created",
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
