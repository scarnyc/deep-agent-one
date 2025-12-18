"""Integration tests for EventTransformer.

Tests real transformation logic for LangGraph events → UI-compatible format.
Focuses on business logic and data transformation, not trivial pass-through tests.
"""

import pytest

from backend.deep_agent.services.event_transformer import EventTransformer


@pytest.fixture
def transformer():
    """Create EventTransformer instance."""
    return EventTransformer()


class TestToolEventTransformation:
    """Test tool event transformations (business logic)."""

    def test_transform_tool_start_creates_running_state(self, transformer) -> None:
        """Test on_tool_start → on_tool_call transformation with correct status."""
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

        # Verify transformation creates correct structure
        assert result["event"] == "on_tool_call"
        data = result["data"]
        assert data["id"] == "tool-123"
        assert data["name"] == "web_search"
        assert data["args"] == {"query": "latest AI news", "max_results": 5}
        assert data["result"] is None
        assert data["status"] == "running"
        assert data["started_at"] is not None
        assert data["completed_at"] is None
        assert data["error"] is None

        # Verify metadata is preserved
        assert result["metadata"]["thread_id"] == "thread-456"
        assert result["metadata"]["trace_id"] == "trace-789"

    def test_transform_tool_end_creates_completed_state(self, transformer) -> None:
        """Test on_tool_end → on_tool_call transformation with result."""
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

        # Verify transformation creates completed status with result
        assert result["event"] == "on_tool_call"
        data = result["data"]
        assert data["id"] == "tool-123"
        assert data["name"] == "web_search"
        assert data["args"] == {"query": "latest AI news"}
        assert data["result"] == "Found 5 sources for 'latest AI news'..."
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_transform_tool_with_missing_fields_uses_defaults(self, transformer) -> None:
        """Test defensive behavior: missing fields get fallback values."""
        langgraph_event = {
            "event": "on_tool_start",
            # Missing: run_id, name, data
        }

        result = transformer.transform(langgraph_event)

        # Should work with fallback values
        assert result["event"] == "on_tool_call"
        assert result["data"]["name"] == "unknown_tool"
        assert result["data"]["args"] == {}
        assert result["data"]["status"] == "running"


class TestChainEventTransformation:
    """Test chain event transformations (business logic)."""

    def test_transform_chain_start_creates_running_step(self, transformer) -> None:
        """Test on_chain_start → on_step transformation."""
        langgraph_event = {
            "event": "on_chain_start",
            "run_id": "step-123",
            "name": "Agent Planning",
            "data": {"context": "initial planning"},
            "metadata": {"thread_id": "thread-456"},
        }

        result = transformer.transform(langgraph_event)

        # Verify step structure
        assert result["event"] == "on_step"
        data = result["data"]
        assert data["id"] == "step-123"
        assert data["name"] == "Agent Planning"
        assert data["status"] == "running"
        assert data["started_at"] is not None
        assert data["completed_at"] is None
        assert data["metadata"] == {"context": "initial planning"}

    def test_transform_chain_end_creates_completed_step(self, transformer) -> None:
        """Test on_chain_end → on_step transformation."""
        langgraph_event = {
            "event": "on_chain_end",
            "run_id": "step-123",
            "name": "Agent Planning",
            "data": {"output": "Plan created successfully"},
            "metadata": {},
        }

        result = transformer.transform(langgraph_event)

        # Verify completed step
        assert result["event"] == "on_step"
        data = result["data"]
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        assert data["metadata"] == {"output": "Plan created successfully"}

    def test_transform_chain_with_missing_fields_uses_defaults(self, transformer) -> None:
        """Test defensive behavior for chain events."""
        langgraph_event = {
            "event": "on_chain_start",
            # Missing: run_id, name, data
        }

        result = transformer.transform(langgraph_event)

        # Should work with fallback values
        assert result["event"] == "on_step"
        assert result["data"]["name"] == "Processing"
        assert result["data"]["status"] == "running"


class TestEventTransformerDefensiveBehavior:
    """Test defensive programming and error handling."""

    def test_transform_handles_none_metadata(self, transformer) -> None:
        """Test transformation when metadata field is missing."""
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
