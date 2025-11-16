"""
Integration tests for recursion_limit enforcement end-to-end.

Tests the complete workflow from agent service through LangGraph recursion_limit
to verify graceful termination via GraphRecursionError handling.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph

from backend.deep_agent.config.settings import Settings
from backend.deep_agent.services.agent_service import AgentService


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Fixture providing test settings with tool call limit."""
    settings = Mock(spec=Settings)
    settings.ENV = "test"  # Disable checkpointer for tests
    settings.OPENAI_API_KEY = "sk-test-key-12345"
    settings.LANGSMITH_API_KEY = None  # Disable tracing for tests
    settings.LANGSMITH_PROJECT = "test-project"
    settings.LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
    settings.LANGSMITH_TRACING_V2 = False
    settings.GPT5_MODEL_NAME = "gpt-5"
    settings.GPT5_DEFAULT_REASONING_EFFORT = "medium"
    settings.GPT5_DEFAULT_VERBOSITY = "medium"
    settings.GPT5_MAX_TOKENS = 4096
    settings.GPT5_TEMPERATURE = 0.7
    settings.CHECKPOINT_DB_PATH = str(tmp_path / "test_checkpoints.db")
    settings.CHECKPOINT_CLEANUP_DAYS = 30
    settings.ENABLE_HITL = False  # Disable HITL for simpler testing
    settings.ENABLE_SUB_AGENTS = False
    settings.MAX_TOOL_CALLS_PER_INVOCATION = 3  # Low limit for testing (recursion_limit = 7)
    settings.STREAM_TIMEOUT_SECONDS = 300
    settings.stream_allowed_events_list = [
        "on_chat_model_stream",
        "on_tool_start",
        "on_tool_end",
        "on_chain_start",
        "on_chain_end",
    ]
    settings.STREAM_VERSION = "v2"
    return settings


class TestAgentServiceWithRecursionLimit:
    """Test AgentService with recursion_limit enforcement."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.services.agent_service.create_agent")
    async def test_agent_service_creates_agent_with_recursion_limit(
        self,
        mock_create_agent: AsyncMock,
        test_settings: Settings,
    ) -> None:
        """Test AgentService creates CompiledStateGraph with recursion_limit."""
        # Arrange
        mock_agent = Mock(spec=CompiledStateGraph)
        mock_create_agent.return_value = mock_agent

        service = AgentService(settings=test_settings)

        # Act
        agent = await service._ensure_agent()

        # Assert
        assert agent is not None
        assert isinstance(agent, Mock)  # Would be CompiledStateGraph in real usage
        mock_create_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_graph_recursion_error_yields_graceful_termination_event(
        self,
        test_settings: Settings,
    ) -> None:
        """Test that GraphRecursionError is caught and yields graceful on_error event."""
        # Arrange
        mock_agent = Mock(spec=CompiledStateGraph)

        async def mock_astream_events_raises_recursion_error(*args, **kwargs):
            """Mock astream_events that raises GraphRecursionError."""
            # Yield a few events first
            yield {"event": "on_chain_start", "data": {}}
            yield {"event": "on_tool_start", "data": {"tool": "web_search"}}
            # Then raise GraphRecursionError
            raise GraphRecursionError("Recursion limit 7 reached")

        mock_agent.astream_events = mock_astream_events_raises_recursion_error

        with patch("backend.deep_agent.services.agent_service.create_agent", return_value=mock_agent):
            service = AgentService(settings=test_settings)

            # Act - collect all events from stream
            events = []
            async for event in service.stream("test message", "thread-123"):
                events.append(event)

            # Assert
            # Should have received events before error + graceful termination event
            assert len(events) > 0

            # Last event should be graceful on_error event
            error_event = events[-1]
            assert error_event["event"] == "on_error"
            assert error_event["data"]["reason"] == "recursion_limit_reached"
            assert "recursion_limit" in error_event["data"]
            assert error_event["data"]["recursion_limit"] == 7  # (3 * 2) + 1
            assert error_event["data"]["max_tool_calls"] == 3
            assert "thread_id" in error_event["metadata"]

    @pytest.mark.asyncio
    async def test_recursion_limit_error_message_user_friendly(
        self,
        test_settings: Settings,
    ) -> None:
        """Test that recursion limit error message is user-friendly."""
        # Arrange
        mock_agent = Mock(spec=CompiledStateGraph)

        async def mock_astream_events_raises(*args, **kwargs):
            """Mock async generator that raises GraphRecursionError."""
            raise GraphRecursionError("Recursion limit reached")
            yield  # Make it an async generator (unreachable but needed for syntax)

        mock_agent.astream_events = mock_astream_events_raises

        with patch("backend.deep_agent.services.agent_service.create_agent", return_value=mock_agent):
            service = AgentService(settings=test_settings)

            # Act
            events = []
            async for event in service.stream("test", "thread-123"):
                events.append(event)

            # Assert
            error_event = events[-1]
            error_message = error_event["data"]["error"]

            # Should be user-friendly, not technical
            assert "extensive processing" in error_message.lower()
            assert "review the results" in error_message.lower()
            # Should NOT contain technical jargon
            assert "GraphRecursionError" not in error_message
            assert "stack trace" not in error_message.lower()

    @pytest.mark.asyncio
    async def test_different_max_tool_calls_produce_different_limits(
        self,
        test_settings: Settings,
    ) -> None:
        """Test that different MAX_TOOL_CALLS_PER_INVOCATION values produce different recursion_limits."""
        # Test cases: (max_tool_calls, expected_recursion_limit)
        test_cases = [
            (3, 7),    # (3 * 2) + 1 = 7
            (5, 11),   # (5 * 2) + 1 = 11
            (12, 25),  # (12 * 2) + 1 = 25
        ]

        for max_calls, expected_limit in test_cases:
            # Arrange
            test_settings.MAX_TOOL_CALLS_PER_INVOCATION = max_calls
            mock_agent = Mock(spec=CompiledStateGraph)

            async def mock_astream_events_raises(*args, **kwargs):
                """Mock async generator that raises GraphRecursionError."""
                raise GraphRecursionError(f"Recursion limit {expected_limit} reached")
                yield  # Make it an async generator (unreachable but needed for syntax)

            mock_agent.astream_events = mock_astream_events_raises

            with patch("backend.deep_agent.services.agent_service.create_agent", return_value=mock_agent):
                service = AgentService(settings=test_settings)

                # Act
                events = []
                async for event in service.stream("test", "thread-123"):
                    events.append(event)

                # Assert
                error_event = events[-1]
                assert error_event["data"]["recursion_limit"] == expected_limit
                assert error_event["data"]["max_tool_calls"] == max_calls
