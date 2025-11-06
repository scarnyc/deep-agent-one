"""Integration tests for tool event streaming through agent_service.py.

This test suite verifies that tool execution events (on_tool_call_start,
on_tool_call_end) stream correctly to the frontend and are not filtered out
by the event filter in agent_service.py.

Regression test for issue: Tool events not displaying on frontend
LangSmith trace: e2eaaf57-67f2-4f2b-9143-9eb9fcdc8f06
"""

import pytest
from typing import List, Dict, Any
from backend.deep_agent.config.settings import get_settings


class TestToolEventStreaming:
    """Test tool event streaming through the event filter."""

    @pytest.fixture
    def settings(self):
        """Get application settings."""
        return get_settings()

    @pytest.fixture
    def allowed_events(self, settings):
        """Get set of allowed event types from settings."""
        return set(settings.stream_allowed_events_list)

    def test_tool_call_events_in_allowed_list(self, allowed_events):
        """Verify tool call event types are in allowed events list.

        This test ensures that both LangGraph v1 (on_tool_*) and v2
        (on_tool_call_*) event patterns are included in STREAM_ALLOWED_EVENTS.
        """
        # LangGraph v2 events (used by current version)
        assert "on_tool_call_start" in allowed_events, \
            "on_tool_call_start must be in STREAM_ALLOWED_EVENTS for tool visibility"
        assert "on_tool_call_end" in allowed_events, \
            "on_tool_call_end must be in STREAM_ALLOWED_EVENTS for tool visibility"

        # LangGraph v1 events (for backward compatibility)
        assert "on_tool_start" in allowed_events, \
            "on_tool_start should be in STREAM_ALLOWED_EVENTS for compatibility"
        assert "on_tool_end" in allowed_events, \
            "on_tool_end should be in STREAM_ALLOWED_EVENTS for compatibility"

    def test_essential_events_in_allowed_list(self, allowed_events):
        """Verify essential event types are in allowed events list."""
        essential_events = [
            "on_chain_start",
            "on_chain_end",
            "on_chat_model_stream",
            "on_llm_start",
            "on_llm_end",
        ]

        for event_type in essential_events:
            assert event_type in allowed_events, \
                f"{event_type} must be in STREAM_ALLOWED_EVENTS"

    def test_parallel_tool_execution_events_filter(self, allowed_events):
        """Test event filtering for parallel tool execution scenario.

        Simulates the scenario from trace e2eaaf57 where 10 parallel web_search
        tool calls were executed. Verifies all tool events pass through filter.
        """
        # Create mock events for 10 parallel tool calls
        tool_start_events = [
            {
                "event": "on_tool_call_start",
                "name": f"web_search_{i}",
                "data": {"input": {"query": f"query_{i}"}},
            }
            for i in range(10)
        ]

        tool_end_events = [
            {
                "event": "on_tool_call_end",
                "name": f"web_search_{i}",
                "data": {"output": {"results": []}},
            }
            for i in range(10)
        ]

        all_events = tool_start_events + tool_end_events

        # Filter events
        passed_events = [
            e for e in all_events
            if e["event"] in allowed_events
        ]

        # Verify all 20 tool events pass through
        assert len(passed_events) == 20, \
            f"Expected 20 tool events to pass, got {len(passed_events)}"

        # Verify both start and end events present
        start_events = [e for e in passed_events if "start" in e["event"]]
        end_events = [e for e in passed_events if "end" in e["event"]]

        assert len(start_events) == 10, \
            f"Expected 10 tool start events, got {len(start_events)}"
        assert len(end_events) == 10, \
            f"Expected 10 tool end events, got {len(end_events)}"

    def test_stream_timeout_sufficient_for_parallel_tools(self, settings):
        """Verify stream timeout is sufficient for parallel tool execution.

        With 10 parallel tool calls taking ~14s max + model processing,
        the timeout must be >60s to prevent premature cancellation.
        """
        min_recommended_timeout = 60  # Original timeout that caused CancelledError
        assert settings.STREAM_TIMEOUT_SECONDS > min_recommended_timeout, \
            f"STREAM_TIMEOUT_SECONDS ({settings.STREAM_TIMEOUT_SECONDS}s) " \
            f"should be > {min_recommended_timeout}s for parallel tool execution"

        # Verify timeout is reasonable (not too high)
        max_reasonable_timeout = 300  # 5 minutes
        assert settings.STREAM_TIMEOUT_SECONDS <= max_reasonable_timeout, \
            f"STREAM_TIMEOUT_SECONDS ({settings.STREAM_TIMEOUT_SECONDS}s) " \
            f"should be <= {max_reasonable_timeout}s"

    def test_event_filter_logic(self, allowed_events):
        """Test the event filtering logic matches agent_service.py behavior."""

        def filter_events(events: List[Dict[str, Any]]) -> tuple:
            """Simulate agent_service.py event filtering."""
            passed = []
            filtered = []

            for event in events:
                event_type = event.get("event", "unknown")
                if event_type in allowed_events:
                    passed.append(event)
                else:
                    filtered.append(event)

            return passed, filtered

        # Test events including tool calls
        test_events = [
            {"event": "on_chain_start", "name": "model"},
            {"event": "on_tool_call_start", "name": "web_search"},
            {"event": "on_tool_call_end", "name": "web_search"},
            {"event": "on_chat_model_stream", "name": "ChatOpenAI"},
            {"event": "on_chain_end", "name": "model"},
            {"event": "on_chain_stream", "name": "model"},  # Should be filtered
        ]

        passed, filtered = filter_events(test_events)

        # Verify tool events pass through
        tool_events = [e for e in passed if "tool" in e["event"]]
        assert len(tool_events) == 2, \
            f"Expected 2 tool events to pass, got {len(tool_events)}"

        # Verify on_chain_stream is filtered (not in allowed events)
        chain_stream_filtered = any(
            e["event"] == "on_chain_stream" for e in filtered
        )
        assert chain_stream_filtered, \
            "on_chain_stream should be filtered (not in allowed events)"

    def test_stream_version_configuration(self, settings):
        """Verify stream version is correctly configured for LangGraph."""
        # Should use v2 for latest LangGraph
        assert settings.STREAM_VERSION in ["v1", "v2"], \
            f"STREAM_VERSION must be 'v1' or 'v2', got '{settings.STREAM_VERSION}'"

    @pytest.mark.parametrize("event_type,should_pass", [
        ("on_tool_call_start", True),
        ("on_tool_call_end", True),
        ("on_tool_start", True),
        ("on_tool_end", True),
        ("on_chain_start", True),
        ("on_chain_end", True),
        ("on_chat_model_stream", True),
        ("on_llm_start", True),
        ("on_llm_end", True),
        ("on_chain_stream", False),  # Not in allowed events
        ("on_parser_start", False),  # Not in allowed events
    ])
    def test_individual_event_types(
        self, event_type: str, should_pass: bool, allowed_events
    ):
        """Test individual event types pass/fail correctly."""
        is_allowed = event_type in allowed_events

        if should_pass:
            assert is_allowed, \
                f"{event_type} should be in allowed events but isn't"
        else:
            assert not is_allowed, \
                f"{event_type} shouldn't be in allowed events but is"

    def test_no_duplicate_allowed_events(self, settings):
        """Verify no duplicate event types in STREAM_ALLOWED_EVENTS."""
        allowed_list = settings.stream_allowed_events_list
        unique_events = set(allowed_list)

        assert len(allowed_list) == len(unique_events), \
            f"Duplicate events found in STREAM_ALLOWED_EVENTS: {allowed_list}"

    def test_minimum_allowed_events_count(self, allowed_events):
        """Verify minimum number of allowed event types.

        We need at least: chain start/end, tool start/end (v1 + v2),
        chat stream, llm start/end = minimum 9 event types.
        """
        min_required = 9
        assert len(allowed_events) >= min_required, \
            f"Need at least {min_required} allowed event types, " \
            f"got {len(allowed_events)}: {sorted(allowed_events)}"
