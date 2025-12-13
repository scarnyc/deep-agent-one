"""Tests for Chat API Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.deep_agent.models.chat import (
    ChatRequest,
    ChatResponse,
    Message,
    MessageRole,
    ResponseStatus,
    StreamEvent,
)


class TestMessageRole:
    """Test MessageRole enum."""

    def test_message_role_values(self) -> None:
        """Test all message role enum values."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

    def test_message_role_from_string(self) -> None:
        """Test creating MessageRole from string."""
        assert MessageRole("user") == MessageRole.USER
        assert MessageRole("assistant") == MessageRole.ASSISTANT
        assert MessageRole("system") == MessageRole.SYSTEM


class TestResponseStatus:
    """Test ResponseStatus enum."""

    def test_response_status_values(self) -> None:
        """Test all response status enum values."""
        assert ResponseStatus.SUCCESS == "success"
        assert ResponseStatus.ERROR == "error"
        assert ResponseStatus.PENDING == "pending"

    def test_response_status_from_string(self) -> None:
        """Test creating ResponseStatus from string."""
        assert ResponseStatus("success") == ResponseStatus.SUCCESS
        assert ResponseStatus("error") == ResponseStatus.ERROR
        assert ResponseStatus("pending") == ResponseStatus.PENDING


class TestMessage:
    """Test Message model."""

    def test_valid_message(self) -> None:
        """Test creating a valid message."""
        msg = Message(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)

    def test_message_with_all_roles(self) -> None:
        """Test message creation with all role types."""
        user_msg = Message(role=MessageRole.USER, content="User message")
        assert user_msg.role == MessageRole.USER

        assistant_msg = Message(role=MessageRole.ASSISTANT, content="Assistant message")
        assert assistant_msg.role == MessageRole.ASSISTANT

        system_msg = Message(role=MessageRole.SYSTEM, content="System message")
        assert system_msg.role == MessageRole.SYSTEM

    def test_message_timestamp_auto_generated(self) -> None:
        """Test that timestamp is automatically generated."""
        msg = Message(role=MessageRole.USER, content="Test")
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)

    def test_message_with_custom_timestamp(self) -> None:
        """Test message with custom timestamp."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        msg = Message(role=MessageRole.USER, content="Test", timestamp=custom_time)
        assert msg.timestamp == custom_time

    def test_message_empty_content(self) -> None:
        """Test that empty content is not allowed."""
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="")

    def test_message_whitespace_only_content(self) -> None:
        """Test that whitespace-only content is not allowed."""
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="   ")

    def test_message_long_content(self) -> None:
        """Test message with very long content."""
        long_content = "A" * 10000
        msg = Message(role=MessageRole.USER, content=long_content)
        assert len(msg.content) == 10000

    def test_message_unicode_content(self) -> None:
        """Test message with Unicode characters."""
        msg = Message(role=MessageRole.USER, content="Hello 世界 🌍")
        assert msg.content == "Hello 世界 🌍"

    def test_message_serialization(self) -> None:
        """Test Message serialization to dict."""
        msg = Message(role=MessageRole.USER, content="Test")
        data = msg.model_dump()

        assert data["role"] == "user"
        assert data["content"] == "Test"
        assert "timestamp" in data

    def test_message_deserialization(self) -> None:
        """Test Message deserialization from dict."""
        data = {
            "role": "assistant",
            "content": "Response",
            "timestamp": "2025-01-01T12:00:00",
        }
        msg = Message(**data)

        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Response"


class TestChatRequest:
    """Test ChatRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid chat request."""
        req = ChatRequest(message="Hello", thread_id="user-123")
        assert req.message == "Hello"
        assert req.thread_id == "user-123"

    def test_request_validation_message_required(self) -> None:
        """Test that message is required."""
        with pytest.raises(ValidationError):
            ChatRequest(thread_id="user-123")  # type: ignore

    def test_request_validation_thread_id_required(self) -> None:
        """Test that thread_id is required."""
        with pytest.raises(ValidationError):
            ChatRequest(message="Hello")  # type: ignore

    def test_request_validation_empty_message(self) -> None:
        """Test that empty message is not allowed."""
        with pytest.raises(ValidationError):
            ChatRequest(message="", thread_id="user-123")

    def test_request_validation_whitespace_message(self) -> None:
        """Test that whitespace-only message is not allowed."""
        with pytest.raises(ValidationError):
            ChatRequest(message="   ", thread_id="user-123")

    def test_request_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is not allowed."""
        with pytest.raises(ValidationError):
            ChatRequest(message="Hello", thread_id="")

    def test_request_validation_whitespace_thread_id(self) -> None:
        """Test that whitespace-only thread_id is not allowed."""
        with pytest.raises(ValidationError):
            ChatRequest(message="Hello", thread_id="   ")

    def test_request_with_long_message(self) -> None:
        """Test request with very long message."""
        long_message = "A" * 10000
        req = ChatRequest(message=long_message, thread_id="user-123")
        assert len(req.message) == 10000

    def test_request_with_unicode(self) -> None:
        """Test request with Unicode characters."""
        req = ChatRequest(message="Hello 世界 🌍", thread_id="user-123")
        assert req.message == "Hello 世界 🌍"

    def test_request_with_special_characters(self) -> None:
        """Test request with special characters."""
        req = ChatRequest(
            message="Hello\nWorld\tWith\rSpecial",
            thread_id="user-123",
        )
        assert "\n" in req.message
        assert "\t" in req.message

    def test_request_serialization(self) -> None:
        """Test ChatRequest serialization to dict."""
        req = ChatRequest(message="Hello", thread_id="user-123")
        data = req.model_dump()

        assert data["message"] == "Hello"
        assert data["thread_id"] == "user-123"

    def test_request_deserialization(self) -> None:
        """Test ChatRequest deserialization from dict."""
        data = {
            "message": "Hello",
            "thread_id": "user-456",
        }
        req = ChatRequest(**data)

        assert req.message == "Hello"
        assert req.thread_id == "user-456"

    def test_request_with_metadata(self) -> None:
        """Test request with optional metadata."""
        req = ChatRequest(
            message="Hello",
            thread_id="user-123",
            metadata={"source": "web", "user_id": "12345"},
        )
        assert req.metadata is not None
        assert req.metadata["source"] == "web"
        assert req.metadata["user_id"] == "12345"

    def test_request_default_metadata(self) -> None:
        """Test that metadata defaults to None."""
        req = ChatRequest(message="Hello", thread_id="user-123")
        assert req.metadata is None


class TestChatResponse:
    """Test ChatResponse model."""

    def test_valid_response(self) -> None:
        """Test creating a valid chat response."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there"),
        ]
        resp = ChatResponse(
            messages=messages,
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )

        assert len(resp.messages) == 2
        assert resp.thread_id == "user-123"
        assert resp.status == ResponseStatus.SUCCESS

    def test_response_empty_messages(self) -> None:
        """Test that empty messages list is not allowed."""
        with pytest.raises(ValidationError):
            ChatResponse(
                messages=[],
                thread_id="user-123",
                status=ResponseStatus.SUCCESS,
            )

    def test_response_single_message(self) -> None:
        """Test response with single message."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )

        assert len(resp.messages) == 1
        assert resp.messages[0].content == "Response"

    def test_response_multiple_messages(self) -> None:
        """Test response with multiple messages."""
        messages = [
            Message(role=MessageRole.USER, content="Q1"),
            Message(role=MessageRole.ASSISTANT, content="A1"),
            Message(role=MessageRole.USER, content="Q2"),
            Message(role=MessageRole.ASSISTANT, content="A2"),
        ]
        resp = ChatResponse(
            messages=messages,
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )

        assert len(resp.messages) == 4

    def test_response_with_metadata(self) -> None:
        """Test response with metadata."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
            metadata={"tokens": 100, "model": "gpt-5.1-2025-11-13"},
        )

        assert resp.metadata is not None
        assert resp.metadata["tokens"] == 100
        assert resp.metadata["model"] == "gpt-5.1-2025-11-13"  # Updated to GPT-5.1

    def test_response_default_metadata(self) -> None:
        """Test that metadata defaults to None."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )

        assert resp.metadata is None

    def test_response_all_statuses(self) -> None:
        """Test response with all status types."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")

        success_resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )
        assert success_resp.status == ResponseStatus.SUCCESS

        error_resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.ERROR,
        )
        assert error_resp.status == ResponseStatus.ERROR

        pending_resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.PENDING,
        )
        assert pending_resp.status == ResponseStatus.PENDING

    def test_response_with_error_message(self) -> None:
        """Test response with error message."""
        msg = Message(role=MessageRole.ASSISTANT, content="Error occurred")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.ERROR,
            error="Internal server error",
        )

        assert resp.error == "Internal server error"
        assert resp.status == ResponseStatus.ERROR

    def test_response_default_error(self) -> None:
        """Test that error defaults to None."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )

        assert resp.error is None

    def test_response_serialization(self) -> None:
        """Test ChatResponse serialization to dict."""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi"),
        ]
        resp = ChatResponse(
            messages=messages,
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )
        data = resp.model_dump()

        assert len(data["messages"]) == 2
        assert data["thread_id"] == "user-123"
        assert data["status"] == "success"

    def test_response_deserialization(self) -> None:
        """Test ChatResponse deserialization from dict."""
        data = {
            "messages": [
                {"role": "user", "content": "Hello", "timestamp": "2025-01-01T12:00:00"},
                {"role": "assistant", "content": "Hi", "timestamp": "2025-01-01T12:00:01"},
            ],
            "thread_id": "user-456",
            "status": "success",
        }
        resp = ChatResponse(**data)

        assert len(resp.messages) == 2
        assert resp.thread_id == "user-456"
        assert resp.status == ResponseStatus.SUCCESS


class TestStreamEvent:
    """Test StreamEvent model."""

    def test_valid_stream_event(self) -> None:
        """Test creating a valid stream event."""
        event = StreamEvent(
            event_type="on_chat_model_stream",
            data={"content": "Hello"},
        )

        assert event.event_type == "on_chat_model_stream"
        assert event.data["content"] == "Hello"
        assert isinstance(event.timestamp, datetime)

    def test_stream_event_timestamp_auto_generated(self) -> None:
        """Test that timestamp is automatically generated."""
        event = StreamEvent(event_type="test_event", data={})
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_stream_event_with_custom_timestamp(self) -> None:
        """Test stream event with custom timestamp."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        event = StreamEvent(
            event_type="test_event",
            data={},
            timestamp=custom_time,
        )
        assert event.timestamp == custom_time

    def test_stream_event_empty_data(self) -> None:
        """Test stream event with empty data."""
        event = StreamEvent(event_type="test_event", data={})
        assert event.data == {}

    def test_stream_event_complex_data(self) -> None:
        """Test stream event with complex data."""
        complex_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "metadata": {"tokens": 10},
            "nested": {"key": "value"},
        }
        event = StreamEvent(event_type="test_event", data=complex_data)

        assert event.data["messages"][0]["role"] == "user"
        assert event.data["metadata"]["tokens"] == 10
        assert event.data["nested"]["key"] == "value"

    def test_stream_event_validation_event_type_required(self) -> None:
        """Test that event_type is required."""
        with pytest.raises(ValidationError):
            StreamEvent(data={})  # type: ignore

    def test_stream_event_validation_data_required(self) -> None:
        """Test that data is required."""
        with pytest.raises(ValidationError):
            StreamEvent(event_type="test_event")  # type: ignore

    def test_stream_event_validation_empty_event_type(self) -> None:
        """Test that empty event_type is not allowed."""
        with pytest.raises(ValidationError):
            StreamEvent(event_type="", data={})

    def test_stream_event_serialization(self) -> None:
        """Test StreamEvent serialization to dict."""
        event = StreamEvent(
            event_type="on_chat_model_stream",
            data={"content": "Hello"},
        )
        data = event.model_dump()

        assert data["event_type"] == "on_chat_model_stream"
        assert data["data"]["content"] == "Hello"
        assert "timestamp" in data

    def test_stream_event_deserialization(self) -> None:
        """Test StreamEvent deserialization from dict."""
        data = {
            "event_type": "on_chat_model_stream",
            "data": {"content": "Hello"},
            "timestamp": "2025-01-01T12:00:00",
        }
        event = StreamEvent(**data)

        assert event.event_type == "on_chat_model_stream"
        assert event.data["content"] == "Hello"

    def test_stream_event_thread_id_optional(self) -> None:
        """Test that thread_id is optional."""
        event = StreamEvent(event_type="test_event", data={})
        assert event.thread_id is None

    def test_stream_event_with_thread_id(self) -> None:
        """Test stream event with thread_id."""
        event = StreamEvent(
            event_type="test_event",
            data={},
            thread_id="user-123",
        )
        assert event.thread_id == "user-123"
