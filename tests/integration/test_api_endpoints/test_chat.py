"""Integration tests for chat API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from backend.deep_agent.models.chat import ChatRequest, ChatResponse, MessageRole, ResponseStatus


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
def mock_agent_service():
    """Mock AgentService for testing without actual agent execution."""
    with patch("backend.deep_agent.api.v1.chat.AgentService") as mock:
        # Create mock instance
        mock_instance = AsyncMock()
        mock.return_value = mock_instance

        # Mock successful invoke response
        mock_instance.invoke.return_value = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there! How can I help you?"},
            ]
        }

        yield mock_instance


class TestChatEndpoint:
    """Test POST /api/v1/chat endpoint."""

    def test_chat_endpoint_success(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test successful chat request returns valid ChatResponse."""
        # Arrange
        request_data = {
            "message": "Hello, agent!",
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert "messages" in data
        assert "thread_id" in data
        assert "status" in data

        assert data["thread_id"] == "test-thread-123"
        assert data["status"] == "success"
        assert len(data["messages"]) == 2

        # Verify AgentService.invoke was called
        mock_agent_service.invoke.assert_called_once()
        call_args = mock_agent_service.invoke.call_args
        assert call_args[1]["message"] == "Hello, agent!"
        assert call_args[1]["thread_id"] == "test-thread-123"

    def test_chat_endpoint_returns_chat_response_model(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test response conforms to ChatResponse schema."""
        # Arrange
        request_data = {
            "message": "Test message",
            "thread_id": "thread-456",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        # Verify can deserialize to ChatResponse
        data = response.json()
        chat_response = ChatResponse(**data)

        assert chat_response.thread_id == "thread-456"
        assert chat_response.status == ResponseStatus.SUCCESS
        assert len(chat_response.messages) >= 1

    def test_chat_endpoint_validation_empty_message(
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
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 422  # Validation error

        data = response.json()
        assert "detail" in data

    def test_chat_endpoint_validation_whitespace_only_message(
        self,
        client: TestClient,
    ) -> None:
        """Test that whitespace-only message is rejected with 422."""
        # Arrange
        request_data = {
            "message": "   ",  # Whitespace only
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_chat_endpoint_validation_empty_thread_id(
        self,
        client: TestClient,
    ) -> None:
        """Test that empty thread_id is rejected with 422."""
        # Arrange
        request_data = {
            "message": "Hello",
            "thread_id": "",  # Empty thread_id
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_chat_endpoint_validation_missing_message(
        self,
        client: TestClient,
    ) -> None:
        """Test that missing message field is rejected with 422."""
        # Arrange
        request_data = {
            # "message": missing
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_chat_endpoint_validation_missing_thread_id(
        self,
        client: TestClient,
    ) -> None:
        """Test that missing thread_id field is rejected with 422."""
        # Arrange
        request_data = {
            "message": "Hello",
            # "thread_id": missing
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 422

    def test_chat_endpoint_with_metadata(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test chat request with optional metadata."""
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
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

    def test_chat_endpoint_agent_error_handling(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that agent errors are handled gracefully."""
        # Arrange
        request_data = {
            "message": "Test error handling",
            "thread_id": "test-thread-123",
        }

        # Mock agent service to raise an error
        mock_agent_service.invoke.side_effect = RuntimeError("Agent execution failed")

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 500

        data = response.json()
        assert "detail" in data

    def test_chat_endpoint_returns_request_id_header(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test that response includes X-Request-ID header."""
        # Arrange
        request_data = {
            "message": "Hello",
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers or "x-request-id" in response.headers

    def test_chat_endpoint_long_message(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test chat with very long message (stress test)."""
        # Arrange
        long_message = "A" * 5000  # 5000 character message
        request_data = {
            "message": long_message,
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        # Verify long message was passed to agent
        mock_agent_service.invoke.assert_called_once()
        call_args = mock_agent_service.invoke.call_args
        assert len(call_args[1]["message"]) == 5000

    def test_chat_endpoint_unicode_message(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test chat with Unicode characters in message."""
        # Arrange
        unicode_message = "Hello 世界! 🌍 Émoji test"
        request_data = {
            "message": unicode_message,
            "thread_id": "test-thread-123",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        # Verify Unicode was preserved
        mock_agent_service.invoke.assert_called_once()
        call_args = mock_agent_service.invoke.call_args
        assert call_args[1]["message"] == unicode_message


class TestChatEndpointIntegration:
    """Integration tests for chat endpoint with minimal mocking."""

    def test_chat_endpoint_exists(self, client: TestClient) -> None:
        """Test that /api/v1/chat endpoint is registered."""
        # Act: Make request to verify endpoint exists
        response = client.post(
            "/api/v1/chat",
            json={"message": "test", "thread_id": "test"},
        )

        # Assert: Should not be 404 (endpoint exists)
        # May be 500 if AgentService not mocked, but endpoint exists
        assert response.status_code != 404

    def test_chat_endpoint_requires_post_method(self, client: TestClient) -> None:
        """Test that GET requests are rejected."""
        # Act
        response = client.get("/api/v1/chat")

        # Assert
        assert response.status_code == 405  # Method Not Allowed
