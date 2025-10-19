"""Integration tests for WebSocket endpoint (AG-UI events)."""
import json
from typing import Any, AsyncIterator, Dict, Iterator

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from unittest.mock import AsyncMock, patch


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client with WebSocket support.

    Imports app here to avoid circular dependencies and ensure
    fresh app instance for each test.
    """
    from backend.deep_agent.main import app
    return TestClient(app)


@pytest.fixture
def mock_agent_service() -> Iterator[AsyncMock]:
    """Mock AgentService for testing without actual agent execution."""
    with patch("backend.deep_agent.api.v1.websocket.AgentService") as mock:
        # Create mock instance
        mock_instance = AsyncMock()
        mock.return_value = mock_instance

        # Mock successful streaming response
        async def mock_stream(*args: Any, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
            """Mock async generator for streaming events."""
            # Simulate AG-UI Protocol events
            events = [
                {
                    "event": "on_chat_model_start",
                    "data": {"input": "Hello, agent!"},
                },
                {
                    "event": "on_chat_model_stream",
                    "data": {"chunk": {"content": "Hi "}},
                },
                {
                    "event": "on_chat_model_stream",
                    "data": {"chunk": {"content": "there!"}},
                },
                {
                    "event": "on_chat_model_end",
                    "data": {"output": "Hi there!"},
                },
            ]
            for event in events:
                yield event

        # Important: Use side_effect to make stream() return the async generator
        # When stream() is called, it will call mock_stream() which returns the async generator
        def create_stream(*args: Any, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
            return mock_stream(*args, **kwargs)

        mock_instance.stream.side_effect = create_stream

        yield mock_instance


class TestWebSocketEndpoint:
    """Test WebSocket /api/v1/ws endpoint."""

    def test_websocket_connection_establishes(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket connection can be established."""
        # Act & Assert
        with client.websocket_connect("/api/v1/ws") as websocket:
            # Connection successful
            assert websocket is not None

    def test_websocket_accepts_chat_message(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket accepts chat messages and streams responses."""
        # Arrange
        message_data = {
            "type": "chat",
            "message": "Hello, agent!",
            "thread_id": "test-thread-123",
        }

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            # Send chat message
            websocket.send_json(message_data)

            # Receive events
            events = []
            while True:
                try:
                    event = websocket.receive_json()
                    events.append(event)
                    # Stop after receiving end event
                    if event.get("event") == "on_chat_model_end":
                        break
                except:
                    break

        # Assert
        assert len(events) > 0
        # Verify AgentService.stream was called
        mock_agent_service.stream.assert_called_once()

    def test_websocket_streams_multiple_events(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket streams all events from agent."""
        # Arrange
        message_data = {
            "type": "chat",
            "message": "Test streaming",
            "thread_id": "test-thread-456",
        }

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json(message_data)

            # Collect all events
            events = []
            for _ in range(10):  # Max 10 events
                try:
                    event = websocket.receive_json()
                    events.append(event)
                except:
                    break

        # Assert
        # Should receive multiple streaming events
        assert len(events) >= 4  # start + 2 stream + end
        # Verify event structure
        for event in events:
            assert "event" in event
            assert "data" in event

    def test_websocket_validates_message_format(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket validates incoming message format."""
        # Arrange - Invalid message (missing required fields)
        invalid_message = {
            "type": "chat",
            # Missing "message" and "thread_id"
        }

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json(invalid_message)

            # Should receive error response
            response = websocket.receive_json()

        # Assert
        assert response.get("type") == "error" or "error" in response

    def test_websocket_handles_empty_message(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket rejects empty messages."""
        # Arrange
        message_data = {
            "type": "chat",
            "message": "",  # Empty message
            "thread_id": "test-thread-123",
        }

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json(message_data)

            # Should receive error response
            response = websocket.receive_json()

        # Assert
        assert response.get("type") == "error" or "error" in response

    def test_websocket_handles_agent_error(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket handles agent errors gracefully."""
        # Arrange
        message_data = {
            "type": "chat",
            "message": "Test error",
            "thread_id": "test-thread-123",
        }

        # Mock agent to raise error
        async def mock_error_stream(*args: Any, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
            yield {"event": "on_chat_model_start", "data": {}}
            raise RuntimeError("Agent execution failed")

        # Wrap in regular function to properly return async generator
        def create_error_stream(*args: Any, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
            return mock_error_stream(*args, **kwargs)

        mock_agent_service.stream.side_effect = create_error_stream

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json(message_data)

            # Collect events (should include error)
            events = []
            for _ in range(5):
                try:
                    event = websocket.receive_json()
                    events.append(event)
                except:
                    break

        # Assert
        # Should receive at least start event + error event
        assert len(events) >= 1
        # Last event should indicate error
        error_events = [e for e in events if e.get("type") == "error" or e.get("event") == "error"]
        assert len(error_events) >= 1

    def test_websocket_supports_metadata(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket accepts metadata in messages."""
        # Arrange
        message_data = {
            "type": "chat",
            "message": "Hello",
            "thread_id": "test-thread-123",
            "metadata": {
                "user_id": "user-456",
                "source": "web",
            },
        }

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json(message_data)

            # Should stream events successfully
            event = websocket.receive_json()

        # Assert
        assert event is not None
        assert "event" in event or "type" in event

    def test_websocket_handles_concurrent_messages(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket handles multiple messages in sequence."""
        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            # Send first message
            websocket.send_json({
                "type": "chat",
                "message": "First message",
                "thread_id": "test-thread-123",
            })

            # Receive first response events
            first_events = []
            for _ in range(5):
                try:
                    event = websocket.receive_json()
                    first_events.append(event)
                except:
                    break

            # Send second message
            websocket.send_json({
                "type": "chat",
                "message": "Second message",
                "thread_id": "test-thread-123",
            })

            # Receive second response events
            second_events = []
            for _ in range(5):
                try:
                    event = websocket.receive_json()
                    second_events.append(event)
                except:
                    break

        # Assert
        assert len(first_events) > 0
        assert len(second_events) > 0

    def test_websocket_closes_gracefully(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that WebSocket closes gracefully when client disconnects."""
        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            # Send a message
            websocket.send_json({
                "type": "chat",
                "message": "Test",
                "thread_id": "test-thread-123",
            })

            # Close connection explicitly
            websocket.close()

        # Assert - Connection closed without errors
        # (If errors occurred, context manager would raise)

    def test_websocket_thread_id_persistence(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that thread_id is passed correctly to agent service."""
        # Arrange
        thread_id = "persistent-thread-789"
        message_data = {
            "type": "chat",
            "message": "Test thread persistence",
            "thread_id": thread_id,
        }

        # Act
        with client.websocket_connect("/api/v1/ws") as websocket:
            websocket.send_json(message_data)

            # Receive at least one event
            websocket.receive_json()

        # Assert
        mock_agent_service.stream.assert_called_once()
        call_kwargs = mock_agent_service.stream.call_args[1]
        assert call_kwargs["thread_id"] == thread_id


class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoint with minimal mocking."""

    def test_websocket_endpoint_exists(self, client: TestClient) -> None:
        """Test that WebSocket endpoint is registered."""
        # Act
        try:
            with client.websocket_connect("/api/v1/ws"):
                # Connection successful - endpoint exists
                pass
            endpoint_exists = True
        except Exception as e:
            # If error is NOT 404, endpoint exists (might be other error)
            endpoint_exists = "404" not in str(e)

        # Assert
        assert endpoint_exists, "WebSocket endpoint should be registered"

    def test_websocket_rejects_http_requests(self, client: TestClient) -> None:
        """Test that WebSocket endpoint rejects regular HTTP requests."""
        # Act
        response = client.get("/api/v1/ws")

        # Assert
        # Should reject with 4xx error (not a WebSocket upgrade request)
        assert response.status_code >= 400
