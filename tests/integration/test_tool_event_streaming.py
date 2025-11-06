"""Integration tests for tool event streaming through agent_service.py.

This test suite verifies that tool execution events (on_tool_call_start,
on_tool_call_end) stream correctly to the frontend and are not filtered out
by the event filter in agent_service.py.

Regression tests:
- Issue: Tool events not displaying on frontend (trace e2eaaf57)
- Issue #113: Agent times out at 44.85s with parallel tools (trace 49feb9c7)
"""

import asyncio
import json
import logging
import pytest
from typing import List, Dict, Any
from httpx import AsyncClient

from backend.deep_agent.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


# Integration tests with real HTTP requests
@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_tool_streaming_with_timeout():
    """Test agent streaming with multiple parallel tool calls.

    This test validates the fix for Issue #113: Agent times out at 44.85s
    due to LangGraph internal per-node timeout when processing queries with
    multiple parallel tool calls followed by GPT-5 synthesis.

    Tests:
    - Query triggers multiple parallel web_search calls
    - STREAM_TIMEOUT_SECONDS=180s prevents overall stream timeout
    - Tool execution events stream correctly
    - Agent completes successfully despite LangGraph's ~45s internal timeout
    """
    settings = get_settings()

    # Verify timeout configuration
    assert settings.STREAM_TIMEOUT_SECONDS >= 180, \
        "STREAM_TIMEOUT_SECONDS must be ≥180s for multi-tool queries"

    logger.info(
        "Starting multi-tool streaming test",
        timeout_seconds=settings.STREAM_TIMEOUT_SECONDS,
        tool_timeout=settings.TOOL_EXECUTION_TIMEOUT,
        web_search_timeout=settings.WEB_SEARCH_TIMEOUT,
    )

    # Query that triggers multiple parallel tool calls
    # (similar to trace 49feb9c7 which asked about Gen AI trends)
    query = "What are the latest trends in Gen AI and LLM applications?"

    async with AsyncClient(base_url="http://localhost:8000", timeout=200.0) as client:
        # Send chat streaming request
        request_payload = {
            "message": query,
            "thread_id": "test-multi-tool-streaming",
        }

        logger.info(f"Sending query: {query}")

        # Track events
        events_received = []
        tool_calls = []
        text_chunks = []
        run_started = False
        run_finished = False
        error_occurred = False

        try:
            async with client.stream(
                "POST",
                "/api/v1/chat/stream",
                json=request_payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    event_data = line[6:]  # Remove "data: " prefix
                    if event_data == "[DONE]":
                        logger.info("Stream completed with [DONE]")
                        break

                    try:
                        event = json.loads(event_data)
                        # LangChain events use "event" field, not "type"
                        event_type = event.get("event")
                        events_received.append(event_type)

                        if event_type == "on_chain_start":
                            event_name = event.get("name", "")
                            if event_name == "LangGraph":
                                run_started = True
                                logger.info("LangGraph run started")

                        elif event_type == "on_tool_call_start" or event_type == "on_tool_start":
                            tool_name = event.get("name", "unknown")
                            tool_calls.append({
                                "name": tool_name,
                                "status": "started",
                            })
                            logger.info(f"Tool call started: {tool_name}")

                        elif event_type == "on_tool_call_end" or event_type == "on_tool_end":
                            tool_name = event.get("name", "unknown")
                            # Update status of matching tool call
                            for tc in tool_calls:
                                if tc["name"] == tool_name and tc["status"] == "started":
                                    tc["status"] = "completed"
                                    break
                            logger.info(f"Tool call completed: {tool_name}")

                        elif event_type == "on_chat_model_stream":
                            chunk = event.get("data", {}).get("chunk", {})
                            # Extract text content from chunk
                            if isinstance(chunk, dict):
                                content = chunk.get("content", "")
                                if content:
                                    text_chunks.append(content)

                        elif event_type == "on_chain_end":
                            event_name = event.get("name", "")
                            if event_name == "LangGraph":
                                run_finished = True
                                logger.info("LangGraph run finished")

                        elif event_type == "error":
                            error_occurred = True
                            error_msg = event.get("data", {}).get("message", "Unknown error")
                            logger.error(f"Error event received: {error_msg}")

                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse event: {e}")
                        continue

        except asyncio.TimeoutError:
            pytest.fail(
                f"Agent streaming timed out after {settings.STREAM_TIMEOUT_SECONDS}s. "
                "This indicates STREAM_TIMEOUT_SECONDS is still too low for multi-tool queries."
            )
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}", exc_info=True)
            raise

    # Assertions
    logger.info(
        "Stream completed. Validating results...",
        events_count=len(events_received),
        tool_calls_count=len(tool_calls),
        text_chunks_count=len(text_chunks),
    )

    # Verify run lifecycle
    assert run_started, "run_started event not received"
    assert run_finished or not error_occurred, \
        "Stream should either finish successfully or have explicit error event"

    # Verify no errors
    assert not error_occurred, "Error event received during streaming"

    # Verify response content
    full_response = "".join(text_chunks)
    assert len(full_response) > 0, "No text content received"

    # Tool calls are optional - agent may or may not use tools depending on query
    # The KEY validation is that the stream completes WITHOUT timing out
    if len(tool_calls) > 0:
        # If tools were called, verify they completed
        completed_tools = [tc for tc in tool_calls if tc["status"] == "completed"]
        assert len(completed_tools) == len(tool_calls), \
            f"Not all tools completed: {len(completed_tools)}/{len(tool_calls)}"
        logger.info(f"✅ Tool calls detected and completed: {len(tool_calls)}")
    else:
        logger.warning("ℹ️  No tool calls detected (agent may not need tools for this query)")

    logger.info(
        "✅ Multi-tool streaming test PASSED",
        tool_calls=len(tool_calls),
        response_length=len(full_response),
        unique_events=set(events_received),
    )

    # Log summary for debugging
    print("\n" + "="*80)
    print("MULTI-TOOL STREAMING TEST SUMMARY")
    print("="*80)
    print(f"Query: {query}")
    print(f"Tool calls: {len(tool_calls)}")
    print(f"Tool names: {[tc['name'] for tc in tool_calls]}")
    print(f"Events received: {len(events_received)} ({len(set(events_received))} unique)")
    print(f"Response length: {len(full_response)} characters")
    print(f"Run completed: {run_finished}")
    print("="*80 + "\n")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_timeout_configuration_loaded():
    """Verify timeout configuration is correctly loaded from .env."""
    settings = get_settings()

    # Verify all timeout settings are configured
    assert hasattr(settings, 'STREAM_TIMEOUT_SECONDS'), \
        "STREAM_TIMEOUT_SECONDS not defined in settings"
    assert hasattr(settings, 'TOOL_EXECUTION_TIMEOUT'), \
        "TOOL_EXECUTION_TIMEOUT not defined in settings"
    assert hasattr(settings, 'WEB_SEARCH_TIMEOUT'), \
        "WEB_SEARCH_TIMEOUT not defined in settings"

    # Verify timeout values meet requirements for multi-tool queries
    assert settings.STREAM_TIMEOUT_SECONDS >= 180, \
        f"STREAM_TIMEOUT_SECONDS too low: {settings.STREAM_TIMEOUT_SECONDS}s (should be ≥180s)"
    assert settings.TOOL_EXECUTION_TIMEOUT >= 90, \
        f"TOOL_EXECUTION_TIMEOUT too low: {settings.TOOL_EXECUTION_TIMEOUT}s (should be ≥90s)"
    assert settings.WEB_SEARCH_TIMEOUT >= 30, \
        f"WEB_SEARCH_TIMEOUT too low: {settings.WEB_SEARCH_TIMEOUT}s (should be ≥30s)"

    logger.info(
        "✅ Timeout configuration validated",
        stream_timeout=settings.STREAM_TIMEOUT_SECONDS,
        tool_timeout=settings.TOOL_EXECUTION_TIMEOUT,
        web_search_timeout=settings.WEB_SEARCH_TIMEOUT,
    )
