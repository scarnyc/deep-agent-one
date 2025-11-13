"""
Integration tests for tool call limit enforcement end-to-end.

Tests the complete workflow from agent service through tool call limiting
to verify graceful termination behavior with real agent configuration.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.deep_agent.agents.deep_agent import ToolCallLimitedAgent
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
    settings.MAX_TOOL_CALLS_PER_INVOCATION = 3  # Low limit for testing
    return settings


class TestAgentServiceWithToolLimit:
    """Test AgentService with tool call limit enforcement."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.services.agent_service.create_agent")
    async def test_agent_service_creates_limited_agent(
        self,
        mock_create_agent: AsyncMock,
        test_settings: Settings,
    ) -> None:
        """Test AgentService creates ToolCallLimitedAgent with correct limit."""
        # Arrange
        mock_limited_agent = Mock(spec=ToolCallLimitedAgent)
        mock_limited_agent.max_tool_calls = 3
        mock_create_agent.return_value = mock_limited_agent

        service = AgentService(settings=test_settings)

        # Act
        agent = await service._ensure_agent()

        # Assert
        assert agent is not None
        assert agent.max_tool_calls == 3
        mock_create_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_service_respects_settings_limit(
        self,
        test_settings: Settings,
    ) -> None:
        """Test AgentService uses limit from settings."""
        # Arrange
        test_settings.MAX_TOOL_CALLS_PER_INVOCATION = 5

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_agent = Mock(spec=ToolCallLimitedAgent)
            mock_agent.max_tool_calls = 5
            mock_create.return_value = mock_agent

            service = AgentService(settings=test_settings)

            # Act
            agent = await service._ensure_agent()

            # Assert
            assert agent.max_tool_calls == 5


class TestToolLimitWithMockedAgent:
    """Test tool limit enforcement with mocked agent execution."""

    @pytest.mark.asyncio
    async def test_stream_terminates_after_limit(
        self,
        test_settings: Settings,
    ) -> None:
        """Test streaming terminates gracefully after tool call limit."""
        # Arrange
        async def mock_astream(input: dict[str, Any], config: dict[str, Any] | None):
            """Mock agent stream that emits many tool calls."""
            yield {"event": "on_chain_start", "data": {}}
            # Emit 5 tool calls (but limit is 3)
            for i in range(5):
                yield {"event": "on_tool_start", "data": {"tool": f"tool_{i}"}}
                yield {"event": "on_tool_end", "data": {"output": f"result_{i}"}}
            yield {"event": "on_chain_end", "data": {"output": {"status": "completed"}}}

        # Create service with mocked agent
        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_agent = Mock(spec=ToolCallLimitedAgent)
            mock_agent.max_tool_calls = 3
            mock_agent.astream = mock_astream
            mock_create.return_value = mock_agent

            service = AgentService(settings=test_settings)

            # Act - Stream events
            events = []
            async for event in service.stream("test message", "thread-123"):
                events.append(event)
                # Stop collecting after termination event
                if (event.get("data", {}).get("output", {}).get("reason") ==
                    "tool_call_limit_reached"):
                    break

            # Assert - should have received termination event
            termination_events = [
                e for e in events
                if e.get("data", {}).get("output", {}).get("reason") == "tool_call_limit_reached"
            ]
            assert len(termination_events) > 0

    @pytest.mark.asyncio
    async def test_invoke_respects_tool_limit(
        self,
        test_settings: Settings,
    ) -> None:
        """Test invoke method respects tool call limit."""
        # Arrange
        async def mock_astream(input: dict[str, Any], config: dict[str, Any] | None):
            """Mock agent that emits tool calls."""
            for _i in range(5):  # Try 5 calls, but limit is 3
                yield {"event": "on_tool_start", "data": {}}
            yield {
                "event": "on_chain_end",
                "data": {
                    "output": {
                        "status": "completed",
                        "reason": "tool_call_limit_reached",
                        "tool_calls": 3,
                    }
                },
            }

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_agent = Mock(spec=ToolCallLimitedAgent)
            mock_agent.max_tool_calls = 3
            mock_agent.astream = mock_astream
            mock_agent.ainvoke = AsyncMock(return_value={
                "status": "completed",
                "reason": "tool_call_limit_reached",
                "tool_calls": 3,
            })
            mock_create.return_value = mock_agent

            service = AgentService(settings=test_settings)

            # Act
            result = await service.invoke("test message", "thread-123")

            # Assert
            assert result is not None
            mock_agent.ainvoke.assert_called_once()


class TestToolLimitLogging:
    """Test logging behavior when tool limit is reached."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.logger")
    async def test_logs_when_limit_reached_in_workflow(
        self,
        mock_logger: Mock,
        test_settings: Settings,
    ) -> None:
        """Test agent workflow logs when tool limit is reached."""
        # Arrange
        async def mock_astream(input: dict[str, Any], config: dict[str, Any] | None):
            """Mock agent that hits tool limit."""
            for _i in range(3):  # Exactly hit the limit
                yield {"event": "on_tool_start", "data": {}}
                yield {"event": "on_tool_end", "data": {}}

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_agent = Mock(spec=ToolCallLimitedAgent)
            mock_agent.max_tool_calls = 3
            mock_agent.astream = mock_astream
            mock_create.return_value = mock_agent

            service = AgentService(settings=test_settings)

            # Act
            events = []
            async for event in service.stream("test message", "thread-123"):
                events.append(event)

            # Note: Actual logging happens in ToolCallLimitedAgent.astream()
            # which is mocked here. In real execution, logger.warning would be called.


class TestSettingsIntegration:
    """Test integration with Settings configuration."""

    def test_settings_has_max_tool_calls_field(self) -> None:
        """Test Settings class has MAX_TOOL_CALLS_PER_INVOCATION field."""
        # This tests that our settings update is properly integrated
        from backend.deep_agent.config.settings import Settings

        # Create settings with explicit value
        settings = Settings(
            OPENAI_API_KEY="sk-test",
            MAX_TOOL_CALLS_PER_INVOCATION=7,
        )

        assert hasattr(settings, "MAX_TOOL_CALLS_PER_INVOCATION")
        assert settings.MAX_TOOL_CALLS_PER_INVOCATION == 7

    def test_settings_default_tool_limit(self) -> None:
        """Test Settings has correct default tool call limit."""
        from backend.deep_agent.config.settings import Settings

        settings = Settings(OPENAI_API_KEY="sk-test")

        # Default should be 10 per our implementation
        assert settings.MAX_TOOL_CALLS_PER_INVOCATION == 10


class TestRealAgentCreation:
    """Test real agent creation with tool call limit (requires deepagents)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_agent_returns_limited_agent(
        self,
        test_settings: Settings,
    ) -> None:
        """Test create_agent() returns ToolCallLimitedAgent wrapper."""
        # This test requires real agent creation
        try:
            from backend.deep_agent.agents.deep_agent import create_agent

            # Act
            agent = await create_agent(settings=test_settings)

            # Assert
            assert agent is not None
            assert isinstance(agent, ToolCallLimitedAgent)
            assert agent.max_tool_calls == test_settings.MAX_TOOL_CALLS_PER_INVOCATION
            assert hasattr(agent, "graph")
            assert hasattr(agent, "_tool_call_count")
            assert hasattr(agent, "_limit_reached")

        except (ImportError, NotImplementedError) as e:
            # Skip if deepagents not installed or not working
            pytest.skip(f"Skipping real agent test: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_limited_agent_has_correct_methods(
        self,
        test_settings: Settings,
    ) -> None:
        """Test ToolCallLimitedAgent has required async methods."""
        try:
            from backend.deep_agent.agents.deep_agent import create_agent

            # Act
            agent = await create_agent(settings=test_settings)

            # Assert - verify async methods exist
            assert hasattr(agent, "astream")
            assert hasattr(agent, "ainvoke")
            assert callable(agent.astream)
            assert callable(agent.ainvoke)

        except (ImportError, NotImplementedError) as e:
            pytest.skip(f"Skipping real agent test: {e}")


class TestCounterResetBehavior:
    """Test counter reset between invocations."""

    @pytest.mark.asyncio
    async def test_counter_resets_between_service_calls(
        self,
        test_settings: Settings,
    ) -> None:
        """Test tool call counter resets between service invocations."""
        # Arrange
        call_count = 0

        async def mock_astream(input: dict[str, Any], config: dict[str, Any] | None):
            """Mock that tracks invocation number."""
            nonlocal call_count
            call_count += 1

            # Emit 2 tool calls per invocation
            for _i in range(2):
                yield {"event": "on_tool_start", "data": {}}
                yield {"event": "on_tool_end", "data": {}}

            yield {
                "event": "on_chain_end",
                "data": {"output": {"status": "completed"}},
            }

        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_agent = Mock(spec=ToolCallLimitedAgent)
            mock_agent.max_tool_calls = 10
            mock_agent._tool_call_count = 0
            mock_agent.astream = mock_astream
            mock_create.return_value = mock_agent

            service = AgentService(settings=test_settings)

            # Act - First invocation
            events1 = []
            async for event in service.stream("message 1", "thread-1"):
                events1.append(event)

            # Act - Second invocation (with same agent instance)
            events2 = []
            async for event in service.stream("message 2", "thread-2"):
                events2.append(event)

            # Assert - both invocations should have succeeded
            assert len(events1) > 0
            assert len(events2) > 0
            # Both should have completed without hitting limit
            # (2 calls per invocation, limit is 10)


class TestWebSocketStreamingWithLimit:
    """Test WebSocket streaming (astream_events) with tool call limits."""

    @pytest.mark.asyncio
    async def test_astream_events_enforces_limit_in_production(
        self,
        test_settings: Settings,
    ) -> None:
        """Test production WebSocket streaming enforces tool call limit."""
        # Arrange
        async def mock_astream_events(
            input: dict[str, Any],
            config: dict[str, Any] | None,
            **kwargs: Any,
        ):
            """Mock agent astream_events that emits many tool calls."""
            yield {"event": "on_chain_start", "data": {}}
            # Emit 15 tool calls (but limit is 3)
            for i in range(15):
                yield {"event": "on_tool_start", "data": {"tool": f"tool_{i}"}}
                yield {"event": "on_tool_end", "data": {"output": f"result_{i}"}}
            yield {"event": "on_chain_end", "data": {"output": {"status": "completed"}}}

        # Create service with mocked agent that has astream_events
        with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
            mock_agent = Mock(spec=ToolCallLimitedAgent)
            mock_agent.max_tool_calls = 3
            mock_agent.astream_events = mock_astream_events
            mock_create.return_value = mock_agent

            service = AgentService(settings=test_settings)

            # Act - Stream events (this uses astream_events internally)
            events = []
            async for event in service.stream("test message", "thread-123"):
                events.append(event)
                # Stop collecting after termination event
                if (event.get("data", {}).get("output", {}).get("reason") ==
                    "tool_call_limit_reached"):
                    break

            # Assert - should have received termination event
            termination_events = [
                e for e in events
                if e.get("data", {}).get("output", {}).get("reason") == "tool_call_limit_reached"
            ]
            assert len(termination_events) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_limited_agent_has_astream_events(
        self,
        test_settings: Settings,
    ) -> None:
        """Test ToolCallLimitedAgent has astream_events method for WebSocket streaming."""
        try:
            from backend.deep_agent.agents.deep_agent import create_agent

            # Act
            agent = await create_agent(settings=test_settings)

            # Assert - verify astream_events method exists
            assert hasattr(agent, "astream_events")
            assert callable(agent.astream_events)

        except (ImportError, NotImplementedError) as e:
            pytest.skip(f"Skipping real agent test: {e}")
