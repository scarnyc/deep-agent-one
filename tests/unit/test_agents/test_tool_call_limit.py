"""
Unit tests for ToolCallLimitedAgent wrapper.

Tests the tool call limiting functionality that enforces max tool calls
per agent invocation with graceful termination.
"""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from backend.deep_agent.agents.deep_agent import ToolCallLimitedAgent

# Test fixtures


@pytest.fixture
def mock_compiled_graph() -> CompiledStateGraph:
    """Fixture providing a mocked CompiledStateGraph."""
    graph = Mock(spec=CompiledStateGraph)
    graph.nodes = ["__start__", "agent", "__end__"]
    graph.edges = [("__start__", "agent"), ("agent", "__end__")]
    return graph


@pytest.fixture
def tool_events() -> list[dict[str, Any]]:
    """Fixture providing mock tool execution events."""
    return [
        {"event": "on_chain_start", "data": {}},
        {"event": "on_tool_start", "data": {"tool": "web_search"}},
        {"event": "on_tool_end", "data": {"output": "result1"}},
        {"event": "on_tool_start", "data": {"tool": "read_file"}},
        {"event": "on_tool_end", "data": {"output": "result2"}},
        {"event": "on_chain_end", "data": {"output": {"status": "completed"}}},
    ]


async def mock_astream_generator(events: list[dict[str, Any]]) -> AsyncIterator[dict[str, Any]]:
    """Helper to create async generator from event list."""
    for event in events:
        yield event


# Test classes


class TestToolCallLimitedAgentInit:
    """Test ToolCallLimitedAgent initialization."""

    def test_init_with_default_limit(self, mock_compiled_graph: CompiledStateGraph) -> None:
        """Test wrapper initializes with default limit of 10."""
        # Act
        wrapper = ToolCallLimitedAgent(mock_compiled_graph)

        # Assert
        assert wrapper.graph == mock_compiled_graph
        assert wrapper.max_tool_calls == 10
        assert wrapper._tool_call_count == 0
        assert wrapper._limit_reached is False

    def test_init_with_custom_limit(self, mock_compiled_graph: CompiledStateGraph) -> None:
        """Test wrapper initializes with custom limit."""
        # Act
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=5)

        # Assert
        assert wrapper.max_tool_calls == 5
        assert wrapper._tool_call_count == 0

    def test_init_stores_graph_reference(self, mock_compiled_graph: CompiledStateGraph) -> None:
        """Test wrapper stores reference to underlying graph."""
        # Act
        wrapper = ToolCallLimitedAgent(mock_compiled_graph)

        # Assert
        assert wrapper.graph is mock_compiled_graph


class TestToolCallCounting:
    """Test tool call counting logic."""

    @pytest.mark.asyncio
    async def test_counts_tool_calls_v1_events(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper counts tool calls using LangGraph v1 events (on_tool_start)."""
        # Arrange
        events = [
            {"event": "on_tool_start", "data": {}},  # Call 1
            {"event": "on_tool_end", "data": {}},
            {"event": "on_tool_start", "data": {}},  # Call 2
            {"event": "on_tool_end", "data": {}},
            {"event": "on_tool_start", "data": {}},  # Call 3
            {"event": "on_tool_end", "data": {}},
        ]
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=5)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert
        assert wrapper._tool_call_count == 3

    @pytest.mark.asyncio
    async def test_counts_tool_calls_v2_events(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper counts tool calls using LangGraph v2 events (on_tool_call_start)."""
        # Arrange
        events = [
            {"event": "on_tool_call_start", "data": {}},  # Call 1
            {"event": "on_tool_call_end", "data": {}},
            {"event": "on_tool_call_start", "data": {}},  # Call 2
            {"event": "on_tool_call_end", "data": {}},
        ]
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=5)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert
        assert wrapper._tool_call_count == 2

    @pytest.mark.asyncio
    async def test_counts_mixed_v1_and_v2_events(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper counts both v1 and v2 tool events correctly."""
        # Arrange
        events = [
            {"event": "on_tool_start", "data": {}},       # Call 1 (v1)
            {"event": "on_tool_end", "data": {}},
            {"event": "on_tool_call_start", "data": {}},  # Call 2 (v2)
            {"event": "on_tool_call_end", "data": {}},
            {"event": "on_tool_start", "data": {}},       # Call 3 (v1)
            {"event": "on_tool_end", "data": {}},
        ]
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=5)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert
        assert wrapper._tool_call_count == 3

    @pytest.mark.asyncio
    async def test_ignores_non_tool_events(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper only counts tool events, ignores other event types."""
        # Arrange
        events = [
            {"event": "on_chain_start", "data": {}},
            {"event": "on_llm_start", "data": {}},
            {"event": "on_tool_start", "data": {}},  # Only this counts
            {"event": "on_llm_end", "data": {}},
            {"event": "on_chain_end", "data": {}},
        ]
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=5)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert
        assert wrapper._tool_call_count == 1


class TestGracefulTermination:
    """Test graceful termination when limit is reached."""

    @pytest.mark.asyncio
    async def test_terminates_after_limit_reached(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper terminates gracefully after max tool calls."""
        # Arrange - 15 tool calls but limit is 10
        events = []
        for _i in range(15):
            events.append({"event": "on_tool_start", "data": {}})
            events.append({"event": "on_tool_end", "data": {}})
        events.append({"event": "on_chain_end", "data": {}})

        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert - should stop after 10th call
        assert wrapper._tool_call_count == 10
        assert wrapper._limit_reached is True

        # Verify termination event was emitted
        final_event = collected_events[-1]
        assert final_event["event"] == "on_chain_end"
        assert final_event["data"]["output"]["reason"] == "tool_call_limit_reached"
        assert final_event["data"]["output"]["tool_calls"] == 10

    @pytest.mark.asyncio
    async def test_does_not_terminate_below_limit(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper does not terminate if below limit."""
        # Arrange - 5 tool calls, limit is 10
        events = []
        for _i in range(5):
            events.append({"event": "on_tool_start", "data": {}})
            events.append({"event": "on_tool_end", "data": {}})
        events.append({"event": "on_chain_end", "data": {"output": {"status": "completed"}}})

        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert - should NOT terminate early
        assert wrapper._tool_call_count == 5
        assert wrapper._limit_reached is False

        # Should NOT have termination event (only original chain_end)
        tool_limit_events = [
            e for e in collected_events
            if e.get("data", {}).get("output", {}).get("reason") == "tool_call_limit_reached"
        ]
        assert len(tool_limit_events) == 0

    @pytest.mark.asyncio
    async def test_emits_limit_reached_event(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper emits proper limit reached event."""
        # Arrange - exactly 10 tool calls to hit limit
        events = []
        for _i in range(10):
            events.append({"event": "on_tool_start", "data": {}})
            events.append({"event": "on_tool_end", "data": {}})

        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        collected_events = []
        async for event in wrapper.astream({}, {}):
            collected_events.append(event)

        # Assert - verify final event structure
        final_event = collected_events[-1]
        assert final_event["event"] == "on_chain_end"
        assert final_event["data"]["output"]["status"] == "completed"
        assert final_event["data"]["output"]["reason"] == "tool_call_limit_reached"
        assert final_event["data"]["output"]["tool_calls"] == 10


class TestCounterReset:
    """Test counter reset behavior across invocations."""

    @pytest.mark.asyncio
    async def test_counter_resets_between_invocations(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test counter resets for each new invocation."""
        # Arrange
        events1 = [
            {"event": "on_tool_start", "data": {}},
            {"event": "on_tool_end", "data": {}},
        ]
        events2 = [
            {"event": "on_tool_start", "data": {}},
            {"event": "on_tool_end", "data": {}},
        ]

        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act - First invocation
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events1))
        async for _event in wrapper.astream({}, {}):
            pass
        assert wrapper._tool_call_count == 1

        # Act - Second invocation
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events2))
        async for _event in wrapper.astream({}, {}):
            pass

        # Assert - counter should reset to 1 (not accumulate to 2)
        assert wrapper._tool_call_count == 1

    @pytest.mark.asyncio
    async def test_limit_flag_resets_between_invocations(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test limit reached flag resets for each invocation."""
        # Arrange - first invocation hits limit
        events1 = [{"event": "on_tool_start", "data": {}}] * 10
        events2 = [{"event": "on_tool_start", "data": {}}]  # second invocation

        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act - First invocation (hits limit)
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events1))
        async for _event in wrapper.astream({}, {}):
            pass
        assert wrapper._limit_reached is True

        # Act - Second invocation (should reset flag)
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events2))
        async for _event in wrapper.astream({}, {}):
            pass

        # Assert - flag should be reset to False (only 1 call)
        assert wrapper._limit_reached is False


class TestLogging:
    """Test logging behavior for tool call limit."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.logger")
    async def test_logs_when_limit_reached(
        self,
        mock_logger: Mock,
        mock_compiled_graph: CompiledStateGraph,
    ) -> None:
        """Test wrapper logs warning when tool call limit is reached."""
        # Arrange
        events = [{"event": "on_tool_start", "data": {}}] * 10
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        async for _event in wrapper.astream({}, {}):
            pass

        # Assert - verify warning was logged
        mock_logger.warning.assert_called()
        warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("Tool call limit reached" in call for call in warning_calls)

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.logger")
    async def test_logs_graceful_termination(
        self,
        mock_logger: Mock,
        mock_compiled_graph: CompiledStateGraph,
    ) -> None:
        """Test wrapper logs info when gracefully terminating."""
        # Arrange
        events = [{"event": "on_tool_start", "data": {}}] * 10
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        async for _event in wrapper.astream({}, {}):
            pass

        # Assert - verify info log for termination
        mock_logger.info.assert_called()
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("enforced" in call or "terminating" in call for call in info_calls)


class TestLangSmithMetadata:
    """Test LangSmith metadata logging."""

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.get_current_run_tree")
    async def test_adds_langsmith_metadata_when_limit_reached(
        self,
        mock_get_run_tree: Mock,
        mock_compiled_graph: CompiledStateGraph,
    ) -> None:
        """Test wrapper adds metadata to LangSmith trace when limit reached."""
        # Arrange
        mock_run_tree = Mock()
        mock_run_tree.add_metadata = Mock()
        mock_get_run_tree.return_value = mock_run_tree

        events = [{"event": "on_tool_start", "data": {}}] * 10
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        async for _event in wrapper.astream({}, {}):
            pass

        # Assert - verify metadata was added
        mock_run_tree.add_metadata.assert_called_once()
        call_kwargs = mock_run_tree.add_metadata.call_args[0][0]
        assert call_kwargs["tool_limit_reached"] is True
        assert call_kwargs["tool_call_count"] == 10
        assert call_kwargs["max_tool_calls"] == 10

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.get_current_run_tree")
    async def test_handles_langsmith_unavailable_gracefully(
        self,
        mock_get_run_tree: Mock,
        mock_compiled_graph: CompiledStateGraph,
    ) -> None:
        """Test wrapper handles LangSmith being unavailable without crashing."""
        # Arrange - simulate LangSmith not available
        mock_get_run_tree.return_value = None

        events = [{"event": "on_tool_start", "data": {}}] * 10
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act & Assert - should not raise exception
        async for _event in wrapper.astream({}, {}):
            pass

        # Should complete without error
        assert wrapper._tool_call_count == 10


class TestAinvokeMethod:
    """Test ainvoke method with tool call limits."""

    @pytest.mark.asyncio
    async def test_ainvoke_uses_astream_internally(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test ainvoke method internally uses astream for monitoring."""
        # Arrange
        events = [
            {"event": "on_tool_start", "data": {}},
            {"event": "on_tool_end", "data": {}},
            {"event": "on_chain_end", "data": {"output": {"result": "success"}}},
        ]
        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        result = await wrapper.ainvoke({"messages": []}, {"thread_id": "test"})

        # Assert - should have collected final result
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_ainvoke_enforces_tool_limit(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test ainvoke enforces tool call limit."""
        # Arrange - 15 tool calls but limit is 10
        events = []
        for _i in range(15):
            events.append({"event": "on_tool_start", "data": {}})
            events.append({"event": "on_tool_end", "data": {}})
        events.append({"event": "on_chain_end", "data": {"output": {"status": "completed"}}})

        mock_compiled_graph.astream = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        await wrapper.ainvoke({"messages": []}, {"thread_id": "test"})

        # Assert - should have terminated at limit
        assert wrapper._tool_call_count == 10
        assert wrapper._limit_reached is True


class TestAstreamEventsMethod:
    """Test astream_events method with tool call limits (used for production WebSocket streaming)."""

    @pytest.mark.asyncio
    async def test_astream_events_counts_tool_calls(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test astream_events method counts tool calls correctly."""
        # Arrange
        events = [
            {"event": "on_tool_start", "data": {}},  # Call 1
            {"event": "on_tool_end", "data": {}},
            {"event": "on_tool_start", "data": {}},  # Call 2
            {"event": "on_tool_end", "data": {}},
            {"event": "on_tool_start", "data": {}},  # Call 3
            {"event": "on_tool_end", "data": {}},
        ]
        mock_compiled_graph.astream_events = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=5)

        # Act
        collected_events = []
        async for event in wrapper.astream_events({}, {}):
            collected_events.append(event)

        # Assert
        assert wrapper._tool_call_count == 3

    @pytest.mark.asyncio
    async def test_astream_events_enforces_tool_limit(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test astream_events enforces tool call limit and terminates gracefully."""
        # Arrange - 15 tool calls but limit is 10
        events = []
        for _i in range(15):
            events.append({"event": "on_tool_start", "data": {}})
            events.append({"event": "on_tool_end", "data": {}})
        events.append({"event": "on_chain_end", "data": {}})

        mock_compiled_graph.astream_events = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        collected_events = []
        async for event in wrapper.astream_events({}, {}):
            collected_events.append(event)

        # Assert - should stop after 10th call
        assert wrapper._tool_call_count == 10
        assert wrapper._limit_reached is True

        # Verify termination event was emitted
        final_event = collected_events[-1]
        assert final_event["event"] == "on_chain_end"
        assert final_event["data"]["output"]["reason"] == "tool_call_limit_reached"
        assert final_event["data"]["output"]["tool_calls"] == 10

    @pytest.mark.asyncio
    async def test_astream_events_counter_resets(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test astream_events resets counter between invocations."""
        # Arrange
        events1 = [
            {"event": "on_tool_start", "data": {}},
            {"event": "on_tool_end", "data": {}},
        ]
        events2 = [
            {"event": "on_tool_start", "data": {}},
            {"event": "on_tool_end", "data": {}},
        ]

        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act - First invocation
        mock_compiled_graph.astream_events = AsyncMock(return_value=mock_astream_generator(events1))
        async for _event in wrapper.astream_events({}, {}):
            pass
        assert wrapper._tool_call_count == 1

        # Act - Second invocation
        mock_compiled_graph.astream_events = AsyncMock(return_value=mock_astream_generator(events2))
        async for _event in wrapper.astream_events({}, {}):
            pass

        # Assert - counter should reset to 1 (not accumulate to 2)
        assert wrapper._tool_call_count == 1

    @pytest.mark.asyncio
    async def test_astream_events_passes_kwargs(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test astream_events passes kwargs to underlying graph (version, include_names, etc.)."""
        # Arrange
        events = [{"event": "on_chain_start", "data": {}}]
        mock_compiled_graph.astream_events = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        async for _event in wrapper.astream_events(
            {"messages": []},
            {"thread_id": "test"},
            version="v2",
            include_names=["agent"],
        ):
            pass

        # Assert - verify kwargs were passed through
        mock_compiled_graph.astream_events.assert_called_once()
        call_args = mock_compiled_graph.astream_events.call_args
        assert call_args[1]["version"] == "v2"
        assert call_args[1]["include_names"] == ["agent"]

    @pytest.mark.asyncio
    @patch("backend.deep_agent.agents.deep_agent.get_current_run_tree")
    async def test_astream_events_adds_langsmith_metadata(
        self,
        mock_get_run_tree: Mock,
        mock_compiled_graph: CompiledStateGraph,
    ) -> None:
        """Test astream_events adds LangSmith metadata when limit reached."""
        # Arrange
        mock_run_tree = Mock()
        mock_run_tree.add_metadata = Mock()
        mock_get_run_tree.return_value = mock_run_tree

        events = [{"event": "on_tool_start", "data": {}}] * 10
        mock_compiled_graph.astream_events = AsyncMock(return_value=mock_astream_generator(events))
        wrapper = ToolCallLimitedAgent(mock_compiled_graph, max_tool_calls=10)

        # Act
        async for _event in wrapper.astream_events({}, {}):
            pass

        # Assert - verify metadata was added
        mock_run_tree.add_metadata.assert_called_once()
        call_kwargs = mock_run_tree.add_metadata.call_args[0][0]
        assert call_kwargs["tool_limit_reached"] is True
        assert call_kwargs["tool_call_count"] == 10
        assert call_kwargs["max_tool_calls"] == 10


class TestAttributeDelegation:
    """Test attribute delegation to underlying graph."""

    def test_delegates_attribute_access_to_graph(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper delegates unknown attributes to underlying graph."""
        # Arrange
        mock_compiled_graph.custom_attr = "test_value"
        wrapper = ToolCallLimitedAgent(mock_compiled_graph)

        # Act & Assert
        assert wrapper.custom_attr == "test_value"

    def test_delegates_method_calls_to_graph(
        self, mock_compiled_graph: CompiledStateGraph
    ) -> None:
        """Test wrapper delegates unknown method calls to underlying graph."""
        # Arrange
        mock_compiled_graph.custom_method = Mock(return_value="result")
        wrapper = ToolCallLimitedAgent(mock_compiled_graph)

        # Act
        result = wrapper.custom_method()

        # Assert
        assert result == "result"
        mock_compiled_graph.custom_method.assert_called_once()
