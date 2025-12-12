"""
Unit tests for EventTransformer.

Tests transformation logic for LangGraph events → UI-compatible format.
"""

import pytest

from backend.deep_agent.services.event_transformer import EventTransformer


@pytest.fixture
def transformer():
    """Create EventTransformer instance."""
    return EventTransformer()


class TestToolEventTransformation:
    """Test tool event transformations (on_tool_start, on_tool_end)."""

    def test_transform_tool_start(self, transformer):
        """Test on_tool_start → on_tool_call (running)."""
        langgraph_event = {
            "event": "on_tool_start",
            "run_id": "tool-123",
            "name": "web_search",
            "data": {"input": {"query": "latest AI news", "max_results": 5}},
            "metadata": {
                "thread_id": "thread-456",
                "trace_id": "trace-789",
            },
        }

        result = transformer.transform(langgraph_event)

        # Check event type transformed
        assert result["event"] == "on_tool_call"

        # Check data structure
        data = result["data"]
        assert data["id"] == "tool-123"
        assert data["name"] == "web_search"
        assert data["args"] == {"query": "latest AI news", "max_results": 5}
        assert data["result"] is None  # Not available yet
        assert data["status"] == "running"
        assert data["started_at"] is not None
        assert data["completed_at"] is None
        assert data["error"] is None

        # Check metadata preserved
        assert result["metadata"]["thread_id"] == "thread-456"
        assert result["metadata"]["trace_id"] == "trace-789"

    def test_transform_tool_end(self, transformer):
        """Test on_tool_end → on_tool_call (completed)."""
        langgraph_event = {
            "event": "on_tool_end",
            "run_id": "tool-123",
            "name": "web_search",
            "data": {
                "input": {"query": "latest AI news"},
                "output": "Found 5 sources for 'latest AI news'...",
            },
            "metadata": {"thread_id": "thread-456"},
        }

        result = transformer.transform(langgraph_event)

        # Check event type transformed
        assert result["event"] == "on_tool_call"

        # Check data structure
        data = result["data"]
        assert data["id"] == "tool-123"
        assert data["name"] == "web_search"
        assert data["args"] == {"query": "latest AI news"}
        assert data["result"] == "Found 5 sources for 'latest AI news'..."
        assert data["status"] == "completed"
        assert data["started_at"] is None  # Not available in end event
        assert data["completed_at"] is not None
        assert data["error"] is None

        # Check metadata preserved
        assert result["metadata"]["thread_id"] == "thread-456"

    def test_transform_tool_with_missing_fields(self, transformer):
        """Test tool transformation with missing fields (defensive)."""
        langgraph_event = {
            "event": "on_tool_start",
            # Missing run_id, name, data
        }

        result = transformer.transform(langgraph_event)

        # Should still work with fallback values
        assert result["event"] == "on_tool_call"
        assert result["data"]["name"] == "unknown_tool"
        assert result["data"]["args"] == {}
        assert result["data"]["status"] == "running"


class TestChainEventTransformation:
    """Test chain event transformations (on_chain_start, on_chain_end)."""

    def test_transform_chain_start(self, transformer):
        """Test on_chain_start → on_step (running)."""
        langgraph_event = {
            "event": "on_chain_start",
            "run_id": "step-123",
            "name": "Agent Planning",
            "data": {"context": "initial planning"},
            "metadata": {"thread_id": "thread-456"},
        }

        result = transformer.transform(langgraph_event)

        # Check event type transformed
        assert result["event"] == "on_step"

        # Check data structure
        data = result["data"]
        assert data["id"] == "step-123"
        assert data["name"] == "Agent Planning"
        assert data["status"] == "running"
        assert data["started_at"] is not None
        assert data["completed_at"] is None
        assert data["metadata"] == {"context": "initial planning"}

        # Check metadata preserved
        assert result["metadata"]["thread_id"] == "thread-456"

    def test_transform_chain_end(self, transformer):
        """Test on_chain_end → on_step (completed)."""
        langgraph_event = {
            "event": "on_chain_end",
            "run_id": "step-123",
            "name": "Agent Planning",
            "data": {"output": "Plan created successfully"},
            "metadata": {},
        }

        result = transformer.transform(langgraph_event)

        # Check event type transformed
        assert result["event"] == "on_step"

        # Check data structure
        data = result["data"]
        assert data["id"] == "step-123"
        assert data["name"] == "Agent Planning"
        assert data["status"] == "completed"
        assert data["started_at"] is None  # Not available in end event
        assert data["completed_at"] is not None
        assert data["metadata"] == {"output": "Plan created successfully"}

    def test_transform_chain_with_missing_fields(self, transformer):
        """Test chain transformation with missing fields (defensive)."""
        langgraph_event = {
            "event": "on_chain_start",
            # Missing run_id, name, data
        }

        result = transformer.transform(langgraph_event)

        # Should still work with fallback values
        assert result["event"] == "on_step"
        assert result["data"]["name"] == "Processing"
        assert result["data"]["status"] == "running"


class TestPassThroughEvents:
    """Test that unhandled events pass through unchanged."""

    def test_heartbeat_passthrough(self, transformer):
        """Test heartbeat events pass through unchanged."""
        heartbeat_event = {
            "event": "heartbeat",
            "data": {
                "status": "processing",
                "message": "Agent is still processing...",
                "heartbeat_number": 3,
                "elapsed_seconds": 15,
            },
            "metadata": {"thread_id": "thread-456", "timestamp": "2025-11-14T12:00:00Z"},
        }

        result = transformer.transform(heartbeat_event)

        # Should be unchanged
        assert result == heartbeat_event
        assert result["event"] == "heartbeat"
        assert result["data"]["heartbeat_number"] == 3

    def test_chat_model_stream_passthrough(self, transformer):
        """Test on_chat_model_stream passes through unchanged."""
        stream_event = {
            "event": "on_chat_model_stream",
            "data": {"chunk": {"content": "Hello, ", "id": "msg-123"}},
            "metadata": {"thread_id": "thread-456"},
        }

        result = transformer.transform(stream_event)

        # Should be unchanged
        assert result == stream_event
        assert result["event"] == "on_chat_model_stream"
        assert result["data"]["chunk"]["content"] == "Hello, "

    def test_error_event_passthrough(self, transformer):
        """Test on_error events pass through unchanged."""
        error_event = {
            "event": "on_error",
            "data": {"error": "Something went wrong", "error_type": "RuntimeError"},
            "metadata": {},
        }

        result = transformer.transform(error_event)

        # Should be unchanged
        assert result == error_event
        assert result["event"] == "on_error"

    def test_unknown_event_passthrough(self, transformer):
        """Test unknown event types pass through unchanged."""
        unknown_event = {"event": "custom_event_type", "data": {"custom_field": "custom_value"}}

        result = transformer.transform(unknown_event)

        # Should be unchanged
        assert result == unknown_event
        assert result["event"] == "custom_event_type"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_event_field(self, transformer):
        """Test transformation when 'event' field is missing."""
        malformed_event = {"data": {"some": "data"}}

        # Should handle gracefully by passing through
        result = transformer.transform(malformed_event)
        assert result == malformed_event

    def test_empty_event(self, transformer):
        """Test transformation of empty event dict."""
        empty_event = {}

        result = transformer.transform(empty_event)
        assert result == empty_event

    def test_none_metadata(self, transformer):
        """Test transformation when metadata is missing."""
        event = {
            "event": "on_tool_start",
            "run_id": "tool-123",
            "name": "test_tool",
            "data": {"input": {}},
            # No metadata field
        }

        result = transformer.transform(event)

        # Should create empty metadata dict
        assert result["metadata"] == {}
        assert result["event"] == "on_tool_call"
