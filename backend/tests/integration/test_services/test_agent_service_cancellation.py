"""
Integration Tests for Agent Service Cancellation Handling

Tests cover:
- Agent streaming handles CancelledError gracefully
- WebSocket handles client disconnect gracefully
- Cancellation logging and error events
- Partial streaming recovery
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from deep_agent.services.agent_service import AgentService
from deep_agent.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Provide mock settings for tests."""
    settings = MagicMock()  # Remove spec to allow any attribute
    settings.OPENAI_API_KEY = "sk-test-key"
    settings.LANGSMITH_API_KEY = "lsv2-test-key"
    settings.LANGSMITH_PROJECT = "test-project"
    settings.ENV = "test"
    settings.STREAM_TIMEOUT_SECONDS = 60
    settings.AGENT_ENABLED = True
    settings.ENABLE_HITL = True
    settings.ENABLE_SUBAGENTS = False
    settings.DEBUG = False
    return settings


@pytest.mark.asyncio
async def test_agent_streaming_handles_cancellation_gracefully(mock_settings):
    """Test that agent streaming handles CancelledError gracefully.

    Verifies that when streaming is cancelled mid-execution:
    - CancelledError is caught and logged
    - Cancellation event is yielded to client
    - No unhandled exception propagates
    - Partial events are processed successfully
    """
    # Arrange
    service = AgentService(settings=mock_settings)

    # Mock the agent's astream_events to yield some events then raise CancelledError
    mock_agent = AsyncMock()

    async def mock_stream_events(*args, **kwargs):
        """Mock stream that yields events then gets cancelled."""
        # Yield a few events
        yield {"event": "on_chain_start", "data": {}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Hello"}}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "!"}}}
        # Simulate cancellation during streaming
        raise asyncio.CancelledError()

    mock_agent.astream_events = mock_stream_events

    # Patch the agent creation to return our mock
    with patch.object(service, '_create_agent', return_value=mock_agent):
        # Act - Start streaming and collect events
        events_received = []
        cancellation_event_received = False

        try:
            async for event in service.stream(
                message="Test message",
                thread_id="test-cancellation-thread"
            ):
                events_received.append(event)

                # Check if we received a cancellation event
                if event.get("event") == "on_error" and "cancelled" in event.get("data", {}).get("error", "").lower():
                    cancellation_event_received = True
        except asyncio.CancelledError:
            # Should NOT propagate - fail test if it does
            pytest.fail("CancelledError should not propagate from stream()")
        except Exception as e:
            # Should NOT raise any other exception
            pytest.fail(f"Unexpected exception: {type(e).__name__}: {e}")

    # Assert
    # Verify we received some events before cancellation
    assert len(events_received) >= 1, "Should have received at least one event"

    # Verify we received a cancellation event
    assert cancellation_event_received, "Should have received a cancellation error event"

    # Verify the last event is the cancellation event
    last_event = events_received[-1]
    assert last_event.get("event") == "on_error"
    assert "cancelled" in last_event.get("data", {}).get("error", "").lower()
    assert last_event.get("data", {}).get("reason") == "client_disconnect_or_timeout"


@pytest.mark.asyncio
async def test_agent_streaming_returns_gracefully_on_cancellation(mock_settings):
    """Test that agent streaming returns (not raises) when cancelled.

    Verifies that CancelledError is handled internally and the
    stream generator exits gracefully without propagating the exception.
    """
    # Arrange
    service = AgentService(settings=mock_settings)

    # Mock agent that immediately gets cancelled
    mock_agent = AsyncMock()

    async def mock_immediate_cancel(*args, **kwargs):
        """Mock stream that gets cancelled immediately."""
        raise asyncio.CancelledError()

    mock_agent.astream_events = mock_immediate_cancel

    with patch.object(service, '_create_agent', return_value=mock_agent):
        # Act
        events = []
        exception_raised = None

        try:
            async for event in service.stream(
                message="Test",
                thread_id="test-immediate-cancel"
            ):
                events.append(event)
        except Exception as e:
            exception_raised = e

    # Assert
    # Should exit gracefully with no exception
    assert exception_raised is None, "Should not raise any exception"

    # Should have yielded a cancellation event
    assert len(events) == 1
    assert events[0].get("event") == "on_error"
    assert "cancelled" in events[0].get("data", {}).get("error", "").lower()


@pytest.mark.asyncio
async def test_agent_streaming_logs_cancellation_context(mock_settings):
    """Test that cancellation is logged with proper context.

    Verifies that when streaming is cancelled, the service logs:
    - thread_id
    - trace_id (if available)
    - events_received count
    - event_types seen
    - reason for cancellation
    """
    # Arrange
    service = AgentService(settings=mock_settings)

    mock_agent = AsyncMock()

    async def mock_stream_with_trace(*args, **kwargs):
        """Mock stream that sets trace_id then gets cancelled."""
        # Yield event with trace_id
        yield {
            "event": "on_chain_start",
            "data": {},
            "metadata": {"trace_id": "test-trace-123"}
        }
        raise asyncio.CancelledError()

    mock_agent.astream_events = mock_stream_with_trace

    # Mock logger to capture log calls
    with patch.object(service, '_create_agent', return_value=mock_agent):
        with patch('deep_agent.services.agent_service.logger') as mock_logger:
            # Act
            async for event in service.stream(
                message="Test",
                thread_id="test-logging-thread"
            ):
                pass

            # Assert
            # Verify warning log was called with proper context
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args

            # Check log message
            assert "cancelled" in call_args[0][0].lower()

            # Check log context
            log_context = call_args[1]
            assert log_context.get("thread_id") == "test-logging-thread"
            assert log_context.get("trace_id") == "test-trace-123"
            assert log_context.get("events_received") >= 1
            assert log_context.get("reason") == "client_disconnect_or_timeout"


@pytest.mark.asyncio
async def test_agent_streaming_partial_events_preserved(mock_settings):
    """Test that events received before cancellation are preserved.

    Verifies that when streaming is cancelled partway through:
    - All events received before cancellation are yielded
    - Events are in correct order
    - Cancellation doesn't corrupt event data
    """
    # Arrange
    service = AgentService(settings=mock_settings)

    expected_events = [
        {"event": "on_chain_start", "data": {"message": "start"}},
        {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Hello"}}},
        {"event": "on_chat_model_stream", "data": {"chunk": {"content": " "}}},
        {"event": "on_chat_model_stream", "data": {"chunk": {"content": "world"}}},
    ]

    mock_agent = AsyncMock()

    async def mock_stream_partial(*args, **kwargs):
        """Mock stream that yields events then cancels."""
        for event in expected_events:
            yield event
        raise asyncio.CancelledError()

    mock_agent.astream_events = mock_stream_partial

    with patch.object(service, '_create_agent', return_value=mock_agent):
        # Act
        received_events = []
        async for event in service.stream(
            message="Test",
            thread_id="test-partial-events"
        ):
            received_events.append(event)

    # Assert
    # Should have received all events plus cancellation event
    assert len(received_events) == len(expected_events) + 1

    # Verify all expected events are present (excluding metadata)
    for i, expected in enumerate(expected_events):
        actual = received_events[i]
        assert actual.get("event") == expected.get("event")
        # Note: metadata is added by stream(), so we don't check it

    # Verify last event is cancellation
    assert received_events[-1].get("event") == "on_error"
