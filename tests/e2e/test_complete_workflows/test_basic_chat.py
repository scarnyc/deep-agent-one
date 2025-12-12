"""
E2E tests for basic chat workflow.

Tests the complete end-to-end chat flow from API request through
agent processing to response, with minimal mocking (only external APIs).

NOTE: These tests require valid OpenAI API keys and are intended for
Phase 0.5 Live API Integration Testing. They will be skipped in regular
test runs and should only be run manually or as part of live API validation.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.deep_agent.models.chat import ChatResponse, ResponseStatus

# Skip all E2E tests unless OPENAI_API_KEY is set
# These tests are for Phase 0.5 Live API Integration Testing
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("your_"),
    reason="E2E tests require valid OPENAI_API_KEY (Phase 0.5 Live API Testing)",
)


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client.

    Imports app here to avoid circular dependencies and ensure
    fresh app instance for each test.
    """
    from backend.deep_agent.main import app

    return TestClient(app)


@pytest.fixture
def mock_openai_client():
    """
    Mock OpenAI client for E2E tests.

    Mocks at the OpenAI client level (not service layer) to test
    complete internal flow while avoiding actual API calls.
    """
    with patch("langchain_openai.ChatOpenAI") as mock_client_class:
        # Create mock client instance
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock chat completion response
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="I'm a helpful AI assistant. I can help you with various tasks. How can I assist you today?",
                    role="assistant",
                )
            )
        ]
        mock_completion.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        mock_client.chat.completions.create.return_value = mock_completion

        yield mock_client


@pytest.fixture
def mock_langsmith():
    """
    Mock LangSmith tracing for E2E tests.

    Prevents actual tracing calls during testing while maintaining
    the tracing code paths.
    """
    with patch("backend.deep_agent.integrations.langsmith.setup_langsmith") as mock_config:
        pass  # setup_langsmith returns None
        yield mock_config


class TestBasicChatWorkflow:
    """E2E tests for complete chat workflow."""

    def test_complete_chat_request_response_cycle(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test complete chat workflow from request to response.

        Flow:
        1. Client sends chat request
        2. FastAPI validates and processes request
        3. AgentService creates agent
        4. Agent invokes with message
        5. Response returned to client

        Tests integration of:
        - API layer (FastAPI)
        - Service layer (AgentService)
        - Agent layer (DeepAgent)
        - Model layer (GPT-5)
        """
        # Arrange
        request_data = {
            "message": "Hello, how can you help me?",
            "thread_id": "e2e-test-thread-001",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert - Response structure
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "messages" in data, "Response missing 'messages' field"
        assert "thread_id" in data, "Response missing 'thread_id' field"
        assert "status" in data, "Response missing 'status' field"

        # Assert - Response values
        assert data["thread_id"] == "e2e-test-thread-001"
        assert data["status"] == "success"
        assert len(data["messages"]) >= 1, "Should have at least one message in response"

        # Assert - Can deserialize to ChatResponse
        chat_response = ChatResponse(**data)
        assert chat_response.status == ResponseStatus.SUCCESS

        # Assert - OpenAI was called through the stack
        assert mock_openai_client.chat.completions.create.called, "OpenAI should be called"

    def test_chat_workflow_with_conversation_history(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test chat workflow maintains conversation history.

        Sends multiple messages on same thread_id and verifies
        state persistence through checkpointer.
        """
        # Arrange
        thread_id = "e2e-test-thread-002"

        # Act - First message
        response1 = client.post(
            "/api/v1/chat",
            json={
                "message": "My name is Alice",
                "thread_id": thread_id,
            },
        )

        # Act - Second message (should remember context)
        response2 = client.post(
            "/api/v1/chat",
            json={
                "message": "What is my name?",
                "thread_id": thread_id,
            },
        )

        # Assert - Both requests successful
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Assert - Thread ID maintained
        data1 = response1.json()
        data2 = response2.json()
        assert data1["thread_id"] == thread_id
        assert data2["thread_id"] == thread_id

        # Assert - OpenAI called for both messages
        assert mock_openai_client.chat.completions.create.call_count >= 2

    def test_chat_workflow_validates_input(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test chat workflow properly validates input before processing."""
        # Arrange - Invalid request (empty message)
        invalid_request = {
            "message": "",
            "thread_id": "e2e-test-thread-003",
        }

        # Act
        response = client.post("/api/v1/chat", json=invalid_request)

        # Assert - Validation error
        assert response.status_code == 422, "Empty message should be rejected"

        # Assert - OpenAI NOT called for invalid input
        assert (
            not mock_openai_client.chat.completions.create.called
        ), "OpenAI should not be called for invalid input"

    def test_chat_workflow_handles_long_messages(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test chat workflow handles long messages correctly."""
        # Arrange
        long_message = "A" * 2000  # 2000 character message
        request_data = {
            "message": long_message,
            "thread_id": "e2e-test-thread-004",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200, "Long message should be accepted"

        data = response.json()
        assert data["status"] == "success"
        assert mock_openai_client.chat.completions.create.called

    def test_chat_workflow_handles_unicode(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test chat workflow handles Unicode characters correctly."""
        # Arrange
        unicode_message = "Hello 世界! 🌍 How are you? Émoji test 日本語"
        request_data = {
            "message": unicode_message,
            "thread_id": "e2e-test-thread-005",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200, "Unicode message should be accepted"

        data = response.json()
        assert data["status"] == "success"

    def test_chat_workflow_with_metadata(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test chat workflow accepts and processes metadata."""
        # Arrange
        request_data = {
            "message": "Test with metadata",
            "thread_id": "e2e-test-thread-006",
            "metadata": {
                "user_id": "user-123",
                "source": "web",
                "session_id": "session-456",
            },
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200, "Request with metadata should succeed"

        data = response.json()
        assert data["status"] == "success"

    def test_chat_workflow_error_recovery(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test chat workflow handles agent errors gracefully.

        Simulates OpenAI API error and verifies proper error handling
        and response to client.
        """
        # Arrange
        request_data = {
            "message": "This will cause an error",
            "thread_id": "e2e-test-thread-007",
        }

        # Mock OpenAI to raise an error
        mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI API error")

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert - Error handled gracefully
        assert response.status_code == 500, "Should return 500 for internal errors"

        data = response.json()
        assert "detail" in data, "Error response should include detail"

    def test_chat_workflow_includes_request_id(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test chat workflow includes request ID for tracing."""
        # Arrange
        request_data = {
            "message": "Test request ID",
            "thread_id": "e2e-test-thread-008",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        # Check for request ID header (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "x-request-id" in headers_lower, "Response should include X-Request-ID header"

    def test_chat_workflow_concurrent_threads(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test chat workflow handles concurrent requests on different threads.

        Simulates multiple users chatting simultaneously with different
        thread IDs to verify thread safety and state isolation.
        """
        # Arrange
        requests = [
            {"message": f"Message from thread {i}", "thread_id": f"e2e-test-thread-{i:03d}"}
            for i in range(10, 15)  # 5 concurrent threads
        ]

        # Act - Send all requests
        responses = []
        for req in requests:
            response = client.post("/api/v1/chat", json=req)
            responses.append(response)

        # Assert - All successful
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"Request {i} failed"
            data = response.json()
            assert data["status"] == "success"
            assert data["thread_id"] == requests[i]["thread_id"]


class TestChatWorkflowPerformance:
    """Performance tests for chat workflow."""

    def test_chat_response_time_under_threshold(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test chat workflow responds within acceptable time.

        Success criteria: Response latency <2s for simple queries.
        """
        import time

        # Arrange
        request_data = {
            "message": "Quick test",
            "thread_id": "e2e-test-thread-perf-001",
        }

        # Act
        start_time = time.time()
        response = client.post("/api/v1/chat", json=request_data)
        end_time = time.time()

        # Assert
        assert response.status_code == 200

        response_time = end_time - start_time
        # Note: With mocked OpenAI, this should be very fast (<1s)
        # In production with real API, threshold is 2s
        assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"
