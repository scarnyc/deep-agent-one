"""Integration tests for chat streaming API endpoint (SSE)."""

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client with chat router.

    Imports app here to avoid circular dependencies and ensure
    fresh app instance for each test.
    """
    from backend.deep_agent.main import app

    return TestClient(app)


@pytest.fixture
def mock_agent_service() -> Iterator[AsyncMock]:
    """Mock AgentService for testing without actual agent execution."""
    with patch("backend.deep_agent.api.v1.chat.AgentService") as mock:
        # Create mock instance
        mock_instance = AsyncMock()
        mock.return_value = mock_instance

        # Mock successful streaming response
        async def mock_stream(*args: Any, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
            """Mock async generator for streaming events."""
            # Simulate LangChain event stream
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

        # Important: Don't call mock_stream(), just assign the function
        # This makes stream() return an async generator when called
        mock_instance.stream.side_effect = mock_stream

        yield mock_instance


class TestChatStreamEndpoint:
    """Test POST /api/v1/chat/stream endpoint (SSE)."""

    def test_stream_endpoint_returns_sse_content_type(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that streaming endpoint returns text/event-stream content type."""
        # Arrange
        request_data = {
            "message": "Hello, agent!",
            "thread_id": "test-thread-123",
        }

        # Act
        with client.stream("POST", "/api/v1/chat/stream", json=request_data) as response:
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_stream_endpoint_streams_events(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that streaming endpoint emits SSE events."""
        # Arrange
        request_data = {
            "message": "Hello, agent!",
            "thread_id": "test-thread-123",
        }

        # Act
        with client.stream("POST", "/api/v1/chat/stream", json=request_data) as response:
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(line[6:])  # Strip "data: " prefix

        # Assert
        assert len(events) > 0
        assert mock_agent_service.stream.called

    def test_stream_endpoint_calls_agent_service_stream(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that streaming endpoint calls AgentService.stream() method."""
        # Arrange
        request_data = {
            "message": "Test streaming",
            "thread_id": "test-thread-456",
        }

        # Act
        with client.stream("POST", "/api/v1/chat/stream", json=request_data) as response:
            # Consume stream
            list(response.iter_lines())

        # Assert
        mock_agent_service.stream.assert_called_once()
        call_kwargs = mock_agent_service.stream.call_args[1]
        assert call_kwargs["message"] == "Test streaming"
        assert call_kwargs["thread_id"] == "test-thread-456"

    def test_stream_endpoint_validation_empty_message(
        self,
        client: TestClient,
    ) -> None:
        """Test that empty message is rejected with 422."""
        # Arrange
        request_data = {
            "message": "",  # Empty message
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat/stream", json=request_data)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_stream_endpoint_validation_missing_thread_id(
        self,
        client: TestClient,
    ) -> None:
        """Test that missing thread_id is rejected with 422."""
        # Arrange
        request_data = {
            "message": "Hello",
            # "thread_id": missing
        }

        # Act
        response = client.post("/api/v1/chat/stream", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_stream_endpoint_includes_request_id_header(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that streaming response includes X-Request-ID header."""
        # Arrange
        request_data = {
            "message": "Hello",
            "thread_id": "test-thread-123",
        }

        # Act
        with client.stream("POST", "/api/v1/chat/stream", json=request_data) as response:
            # Assert
            assert "X-Request-ID" in response.headers or "x-request-id" in response.headers

    def test_stream_endpoint_handles_agent_error(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that agent errors during streaming are handled gracefully."""
        # Arrange
        request_data = {
            "message": "Test error handling",
            "thread_id": "test-thread-123",
        }

        # Mock agent service to raise an error
        async def mock_error_stream(*args: Any, **kwargs: Any) -> AsyncIterator[dict[str, Any]]:
            """Mock async generator that raises an error."""
            yield {"event": "on_chat_model_start", "data": {}}
            raise RuntimeError("Agent streaming failed")

        # Use side_effect for proper async generator behavior
        mock_agent_service.stream.side_effect = mock_error_stream

        # Act
        with client.stream("POST", "/api/v1/chat/stream", json=request_data) as response:
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(line[6:])

        # Assert
        # Should receive at least one event before error
        # Error handling should prevent stream from crashing
        assert len(events) >= 1  # At least the start event
        # Last event should be an error event
        last_event = json.loads(events[-1])
        assert last_event.get("event_type") == "error"

    def test_stream_endpoint_with_metadata(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test streaming with optional metadata."""
        # Arrange
        request_data = {
            "message": "Hello",
            "thread_id": "test-thread-123",
            "metadata": {
                "user_id": "user-456",
                "source": "web",
            },
        }

        # Act
        with client.stream("POST", "/api/v1/chat/stream", json=request_data) as response:
            # Assert
            assert response.status_code == 200

    def test_stream_endpoint_rate_limiting(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that streaming endpoint enforces rate limiting."""
        # Arrange
        request_data = {
            "message": "Hello",
            "thread_id": "test-thread-123",
        }

        # Act: Make 15 rapid requests (limit is 10/minute)
        # Note: Other tests may have consumed some of the rate limit, so
        # we make more requests to ensure we definitely hit the limit
        responses = []
        for _ in range(15):
            response = client.post("/api/v1/chat/stream", json=request_data)
            responses.append(response)

        # Assert: At least some requests should be rate limited (429)
        # The exact count depends on previous tests, but we should see
        # BOTH successful requests AND rate-limited ones
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)

        # Verify rate limiting is working (at least some requests blocked)
        assert rate_limited_count >= 1, "Rate limiting should block some requests"
        # Verify some requests succeeded (rate limit not too restrictive)
        assert success_count >= 1, "Some requests should succeed before hitting limit"


class TestChatStreamIntegration:
    """Integration tests for streaming endpoint with minimal mocking."""

    def test_stream_endpoint_exists(self, client: TestClient) -> None:
        """Test that /api/v1/chat/stream endpoint is registered."""
        # Act: Make request to verify endpoint exists
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "test", "thread_id": "test"},
        )

        # Assert: Should not be 404 (endpoint exists)
        # May be 500 if AgentService not mocked, but endpoint exists
        assert response.status_code != 404

    def test_stream_endpoint_requires_post_method(self, client: TestClient) -> None:
        """Test that GET requests to stream endpoint are rejected."""
        # Act
        response = client.get("/api/v1/chat/stream")

        # Assert
        assert response.status_code == 405  # Method Not Allowed
