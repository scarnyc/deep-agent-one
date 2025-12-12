"""Integration tests for Agent Management endpoints (HITL workflows)."""

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.deep_agent.models.agents import AgentRunStatus, HITLAction


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
def mock_agent_service() -> Iterator[AsyncMock]:
    """Mock AgentService for testing without actual agent execution."""
    with patch("backend.deep_agent.api.v1.agents.AgentService") as mock:
        # Create mock instance
        mock_instance = AsyncMock()
        mock.return_value = mock_instance

        # Mock get_state() to return agent run state
        async def mock_get_state(*args: Any, **kwargs: Any) -> dict[str, Any]:
            """Mock get_state returning agent run state."""
            return {
                "values": {
                    "messages": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi there!"},
                    ]
                },
                "next": [],  # Empty means completed
                "config": {
                    "configurable": {
                        "thread_id": kwargs.get("thread_id", "test-thread-123"),
                        "checkpoint_id": "checkpoint-abc",
                    }
                },
                "metadata": {},
                "created_at": "2025-01-01T12:00:00",
                "parent_config": None,
            }

        mock_instance.get_state.side_effect = mock_get_state

        # Mock update_state() to confirm HITL approval
        async def mock_update_state(*args: Any, **kwargs: Any) -> None:
            """Mock update_state for HITL approval."""
            pass

        mock_instance.update_state.side_effect = mock_update_state

        yield mock_instance


class TestGetAgentStatus:
    """Test GET /api/v1/agents/{thread_id} endpoint."""

    def test_get_agent_status_success(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test getting agent status returns state information."""
        # Arrange
        thread_id = "test-thread-123"

        # Act
        response = client.get(f"/api/v1/agents/{thread_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "thread_id" in data
        assert "status" in data
        assert data["thread_id"] == thread_id

        # Verify service was called
        mock_agent_service.get_state.assert_called_once()

    def test_get_agent_status_thread_not_found(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test getting status for non-existent thread returns 404."""
        # Arrange
        thread_id = "non-existent-thread"

        # Mock get_state to raise error
        async def mock_get_state_not_found(*args: Any, **kwargs: Any) -> dict[str, Any]:
            raise ValueError(f"Thread not found: {thread_id}")

        mock_agent_service.get_state.side_effect = mock_get_state_not_found

        # Act
        response = client.get(f"/api/v1/agents/{thread_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "error" in data

    def test_get_agent_status_invalid_thread_id(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test getting status with empty thread_id returns 422."""
        # Act
        response = client.get("/api/v1/agents/")

        # Assert - should be 404 or 405 (trailing slash)
        assert response.status_code in [404, 405]

    def test_get_agent_status_running(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test getting status for running agent."""
        # Arrange
        thread_id = "running-thread"

        # Mock state with "next" nodes (indicates still running)
        async def mock_get_state_running(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return {
                "values": {"messages": []},
                "next": ["agent_node"],  # Agent is still running
                "config": {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_id": "checkpoint-123",
                    }
                },
                "metadata": {},
                "created_at": "2025-01-01T12:00:00",
                "parent_config": None,
            }

        mock_agent_service.get_state.side_effect = mock_get_state_running

        # Act
        response = client.get(f"/api/v1/agents/{thread_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["running", AgentRunStatus.RUNNING.value]


class TestApproveHITL:
    """Test POST /api/v1/agents/{thread_id}/approve endpoint."""

    def test_approve_hitl_accept_action(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test approving HITL with ACCEPT action."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.ACCEPT.value,
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=request_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "success" in data
        assert "message" in data
        assert "run_id" in data
        assert "thread_id" in data
        assert data["success"] is True
        assert data["thread_id"] == thread_id

        # Verify service was called
        mock_agent_service.update_state.assert_called_once()

    def test_approve_hitl_respond_action(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test approving HITL with RESPOND action and custom text."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.RESPOND.value,
            "response_text": "User provided custom response",
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=request_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify update_state was called with response text
        mock_agent_service.update_state.assert_called_once()

    def test_approve_hitl_edit_action(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test approving HITL with EDIT action and tool edits."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.EDIT.value,
            "tool_edits": {"query": "Modified search query"},
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=request_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify update_state was called with edits
        mock_agent_service.update_state.assert_called_once()

    def test_approve_hitl_invalid_thread_id(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test approving HITL with invalid thread_id."""
        # Arrange
        request_data = {
            "run_id": "run-456",
            "thread_id": "",  # Empty thread_id
            "action": HITLAction.ACCEPT.value,
        }

        # Act
        response = client.post(
            "/api/v1/agents/invalid-thread/approve",
            json=request_data,
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_approve_hitl_no_pending_request(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test approving HITL when no pending request exists."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.ACCEPT.value,
        }

        # Mock update_state to raise error (no pending HITL)
        async def mock_update_state_no_hitl(*args: Any, **kwargs: Any) -> None:
            raise ValueError("No pending HITL request found")

        mock_agent_service.update_state.side_effect = mock_update_state_no_hitl

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=request_data,
        )

        # Assert
        assert response.status_code == 400  # Bad request
        data = response.json()
        assert "detail" in data or "error" in data

    def test_approve_hitl_validation_error_missing_fields(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test approving HITL with missing required fields."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            # Missing run_id
            "thread_id": thread_id,
            "action": HITLAction.ACCEPT.value,
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=request_data,
        )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_approve_hitl_respond_without_response_text(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test RESPOND action without response_text returns error."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.RESPOND.value,
            # Missing response_text (required for RESPOND)
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=request_data,
        )

        # Assert - should be validation error or handled by endpoint
        assert response.status_code in [400, 422]


class TestRespondHITL:
    """Test POST /api/v1/agents/{thread_id}/respond endpoint (convenience wrapper)."""

    def test_respond_hitl_success(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test responding to HITL with custom text."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.RESPOND.value,
            "response_text": "Custom user response",
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/respond",
            json=request_data,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_respond_hitl_empty_response(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test responding to HITL with empty response text."""
        # Arrange
        thread_id = "test-thread-123"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.RESPOND.value,
            "response_text": "",  # Empty response
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/respond",
            json=request_data,
        )

        # Assert - should validate and reject empty response
        assert response.status_code in [400, 422]

    def test_respond_hitl_thread_not_found(
        self,
        client: TestClient,
        mock_agent_service: AsyncMock,
    ) -> None:
        """Test responding to HITL for non-existent thread."""
        # Arrange
        thread_id = "non-existent-thread"
        request_data = {
            "run_id": "run-456",
            "thread_id": thread_id,
            "action": HITLAction.RESPOND.value,
            "response_text": "Response",
        }

        # Mock update_state to raise error
        async def mock_update_state_not_found(*args: Any, **kwargs: Any) -> None:
            raise ValueError(f"Thread not found: {thread_id}")

        mock_agent_service.update_state.side_effect = mock_update_state_not_found

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/respond",
            json=request_data,
        )

        # Assert
        assert response.status_code == 404
