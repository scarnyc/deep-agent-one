"""Integration tests for Chat API Pydantic models.

This module tests business logic, validation rules, and API contracts
for chat-related models.
"""

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


class TestMessageValidation:
    """Test Message model validation rules."""

    def test_message_empty_content_validation(self) -> None:
        """Test that empty content is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER, content="")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "content" in errors[0]["loc"]
        assert "empty" in str(errors[0]["msg"]).lower()

    def test_message_whitespace_only_content_validation(self) -> None:
        """Test that whitespace-only content is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER, content="   ")

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "content" in errors[0]["loc"]
        assert "empty" in str(errors[0]["msg"]).lower()

    def test_message_long_content_handling(self) -> None:
        """Test message handles very long content (edge case)."""
        long_content = "A" * 10000
        msg = Message(role=MessageRole.USER, content=long_content)
        assert len(msg.content) == 10000
        assert msg.role == MessageRole.USER

    def test_message_unicode_content_handling(self) -> None:
        """Test message handles Unicode characters correctly."""
        msg = Message(role=MessageRole.USER, content="Hello 世界 🌍")
        assert msg.content == "Hello 世界 🌍"
        assert msg.role == MessageRole.USER


class TestChatRequestValidation:
    """Test ChatRequest model validation rules."""

    def test_request_validation_message_required(self) -> None:
        """Test that message field is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(thread_id="user-123")  # type: ignore

        errors = exc_info.value.errors()
        assert any("message" in str(error["loc"]) for error in errors)

    def test_request_validation_thread_id_required(self) -> None:
        """Test that thread_id field is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="Hello")  # type: ignore

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_request_validation_empty_message(self) -> None:
        """Test that empty message is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="", thread_id="user-123")

        errors = exc_info.value.errors()
        assert any("message" in str(error["loc"]) for error in errors)
        assert any("empty" in str(error["msg"]).lower() for error in errors)

    def test_request_validation_whitespace_message(self) -> None:
        """Test that whitespace-only message is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="   ", thread_id="user-123")

        errors = exc_info.value.errors()
        assert any("message" in str(error["loc"]) for error in errors)

    def test_request_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="Hello", thread_id="")

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_request_validation_whitespace_thread_id(self) -> None:
        """Test that whitespace-only thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="Hello", thread_id="   ")

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_request_with_long_message(self) -> None:
        """Test request handles very long message (edge case)."""
        long_message = "A" * 10000
        req = ChatRequest(message=long_message, thread_id="user-123")
        assert len(req.message) == 10000
        assert req.thread_id == "user-123"

    def test_request_with_unicode(self) -> None:
        """Test request handles Unicode characters."""
        req = ChatRequest(message="Hello 世界 🌍", thread_id="user-123")
        assert req.message == "Hello 世界 🌍"

    def test_request_with_special_characters(self) -> None:
        """Test request handles special characters."""
        req = ChatRequest(
            message="Hello\nWorld\tWith\rSpecial",
            thread_id="user-123",
        )
        assert "\n" in req.message
        assert "\t" in req.message

    def test_request_with_metadata(self) -> None:
        """Test request accepts optional metadata."""
        req = ChatRequest(
            message="Hello",
            thread_id="user-123",
            metadata={"source": "web", "user_id": "12345"},
        )
        assert req.metadata is not None
        assert req.metadata["source"] == "web"
        assert req.metadata["user_id"] == "12345"

    def test_request_metadata_size_validation(self) -> None:
        """Test metadata size limit (10KB max) - security constraint."""
        # Create metadata that exceeds 10KB limit
        large_metadata = {"data": "A" * 12000}

        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                message="Hello",
                thread_id="user-123",
                metadata=large_metadata,
            )

        errors = exc_info.value.errors()
        assert any("metadata" in str(error["loc"]) for error in errors)
        assert any("too large" in str(error["msg"]).lower() for error in errors)

    def test_request_metadata_depth_validation(self) -> None:
        """Test metadata depth limit (5 levels max) - security constraint."""
        # Create deeply nested metadata (6 levels deep)
        deep_metadata: dict = {"level1": {}}
        current = deep_metadata["level1"]
        for i in range(2, 7):
            current[f"level{i}"] = {}
            current = current[f"level{i}"]

        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                message="Hello",
                thread_id="user-123",
                metadata=deep_metadata,
            )

        errors = exc_info.value.errors()
        assert any("metadata" in str(error["loc"]) for error in errors)
        assert any("deep" in str(error["msg"]).lower() for error in errors)

    def test_request_metadata_non_json_serializable(self) -> None:
        """Test metadata must be JSON-serializable - security constraint."""

        class NonSerializable:
            pass

        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                message="Hello",
                thread_id="user-123",
                metadata={"obj": NonSerializable()},  # type: ignore
            )

        errors = exc_info.value.errors()
        assert any("metadata" in str(error["loc"]) for error in errors)


class TestChatResponseValidation:
    """Test ChatResponse model validation rules."""

    def test_response_empty_messages_validation(self) -> None:
        """Test that empty messages list is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            ChatResponse(
                messages=[],
                thread_id="user-123",
                status=ResponseStatus.SUCCESS,
            )

        errors = exc_info.value.errors()
        assert any("messages" in str(error["loc"]) for error in errors)

    def test_response_single_message(self) -> None:
        """Test response accepts single message."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
        )

        assert len(resp.messages) == 1
        assert resp.messages[0].content == "Response"
        assert resp.status == ResponseStatus.SUCCESS

    def test_response_multiple_messages(self) -> None:
        """Test response accepts multiple messages."""
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
        assert resp.thread_id == "user-123"

    def test_response_with_metadata(self) -> None:
        """Test response accepts optional metadata."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
            metadata={"tokens": 100, "model": "gpt-5.1-2025-11-13"},
        )

        assert resp.metadata is not None
        assert resp.metadata["tokens"] == 100
        assert resp.metadata["model"] == "gpt-5.1-2025-11-13"

    def test_response_with_error_message(self) -> None:
        """Test response accepts error message with ERROR status."""
        msg = Message(role=MessageRole.ASSISTANT, content="Error occurred")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.ERROR,
            error="Internal server error",
        )

        assert resp.error == "Internal server error"
        assert resp.status == ResponseStatus.ERROR

    def test_response_with_trace_and_run_ids(self) -> None:
        """Test response accepts debugging identifiers."""
        msg = Message(role=MessageRole.ASSISTANT, content="Response")
        resp = ChatResponse(
            messages=[msg],
            thread_id="user-123",
            status=ResponseStatus.SUCCESS,
            trace_id="trace-abc-123",
            run_id="run-def-456",
        )

        assert resp.trace_id == "trace-abc-123"
        assert resp.run_id == "run-def-456"


class TestStreamEventValidation:
    """Test StreamEvent model validation rules."""

    def test_stream_event_validation_event_type_required(self) -> None:
        """Test that event_type is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            StreamEvent(data={})  # type: ignore

        errors = exc_info.value.errors()
        assert any("event_type" in str(error["loc"]) for error in errors)

    def test_stream_event_validation_data_required(self) -> None:
        """Test that data is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            StreamEvent(event_type="test_event")  # type: ignore

        errors = exc_info.value.errors()
        assert any("data" in str(error["loc"]) for error in errors)

    def test_stream_event_validation_empty_event_type(self) -> None:
        """Test that empty event_type is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            StreamEvent(event_type="", data={})

        errors = exc_info.value.errors()
        assert any("event_type" in str(error["loc"]) for error in errors)
        assert any("empty" in str(error["msg"]).lower() for error in errors)

    def test_stream_event_empty_data(self) -> None:
        """Test stream event accepts empty data dict."""
        event = StreamEvent(event_type="test_event", data={})
        assert event.data == {}
        assert event.event_type == "test_event"

    def test_stream_event_complex_data(self) -> None:
        """Test stream event handles complex nested data."""
        complex_data = {
            "messages": [{"role": "user", "content": "Hello"}],
            "metadata": {"tokens": 10},
            "nested": {"key": "value"},
        }
        event = StreamEvent(event_type="test_event", data=complex_data)

        assert event.data["messages"][0]["role"] == "user"
        assert event.data["metadata"]["tokens"] == 10
        assert event.data["nested"]["key"] == "value"

    def test_stream_event_with_thread_id(self) -> None:
        """Test stream event accepts optional thread_id."""
        event = StreamEvent(
            event_type="test_event",
            data={},
            thread_id="user-123",
        )
        assert event.thread_id == "user-123"
