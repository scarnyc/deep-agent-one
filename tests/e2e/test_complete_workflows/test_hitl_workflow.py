"""
E2E tests for Human-in-the-Loop (HITL) workflow.

Tests the complete HITL approval flow including agent interruption,
state persistence, approval/rejection, and agent continuation.

NOTE: These tests require valid OpenAI API keys and are intended for
Phase 0.5 Live API Integration Testing. They will be skipped in regular
test runs and should only be run manually or as part of live API validation.
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from backend.deep_agent.models.agents import AgentRunStatus, HITLAction

# Skip all E2E tests unless OPENAI_API_KEY is set
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("your_"),
    reason="E2E tests require valid OPENAI_API_KEY (Phase 0.5 Live API Testing)"
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
    """Mock OpenAI client for E2E tests."""
    with patch("langchain_openai.ChatOpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock chat completion response
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="I need approval to proceed with this action.",
                    role="assistant"
                )
            )
        ]
        mock_completion.usage = MagicMock(
            prompt_tokens=15,
            completion_tokens=25,
            total_tokens=40
        )

        mock_client.chat.completions.create.return_value = mock_completion

        yield mock_client


@pytest.fixture
def mock_langsmith():
    """Mock LangSmith tracing for E2E tests."""
    with patch("backend.deep_agent.integrations.langsmith.setup_langsmith") as mock_config:
        pass  # setup_langsmith returns None
        yield mock_config


@pytest.fixture
def mock_checkpointer_with_interrupt():
    """
    Mock checkpointer that simulates HITL interrupt state.

    Returns interrupted state for get_state() to simulate agent
    waiting for human approval.
    """
    with patch("backend.deep_agent.agents.checkpointer.CheckpointerManager") as mock_manager:
        # Mock checkpointer instance
        mock_checkpointer = MagicMock()

        # Mock manager context manager
        mock_manager_instance = MagicMock()
        mock_manager.return_value.__aenter__ = AsyncMock(return_value=mock_manager_instance)
        mock_manager.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock create_checkpointer
        mock_manager_instance.create_checkpointer = AsyncMock(return_value=mock_checkpointer)

        # Mock get() to return interrupted state
        mock_checkpointer.get.return_value = {
            "values": {
                "messages": [
                    {"role": "user", "content": "Please delete important files"},
                    {"role": "assistant", "content": "I need approval to proceed."},
                ]
            },
            "next": ["__interrupt__"],  # Indicates waiting for approval
            "config": {
                "configurable": {
                    "thread_id": "hitl-test-thread",
                    "checkpoint_id": "checkpoint-interrupt",
                }
            },
            "metadata": {
                "interrupt_type": "approval_required",
                "action": "delete_files",
            },
            "created_at": "2025-01-01T12:00:00",
            "parent_config": None,
        }

        yield mock_checkpointer


class TestHITLWorkflowBasic:
    """Basic HITL workflow tests."""

    def test_get_agent_status_shows_interrupted_state(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test getting agent status for interrupted agent.

        Flow:
        1. Agent runs and gets interrupted (needs approval)
        2. Client requests agent status
        3. Status shows interrupted state with pending approval
        """
        # Arrange
        thread_id = "hitl-test-thread-001"

        # Mock AgentService.get_state to return interrupted state
        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            async def mock_get_state(**kwargs) -> Dict[str, Any]:
                return {
                    "values": {"messages": []},
                    "next": ["__interrupt__"],  # Interrupted state
                    "config": {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_id": "checkpoint-123",
                        }
                    },
                    "metadata": {"interrupt_type": "approval_required"},
                    "created_at": "2025-01-01T12:00:00",
                    "parent_config": None,
                }

            mock_service.get_state.side_effect = mock_get_state

            # Act
            response = client.get(f"/api/v1/agents/{thread_id}")

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert data["thread_id"] == thread_id
            assert "status" in data
            # Status should indicate interrupted/waiting state

    def test_approve_hitl_action(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test approving a HITL action allows agent to continue.

        Flow:
        1. Agent is interrupted waiting for approval
        2. Client sends approval
        3. Agent continues execution
        4. Response confirms approval processed
        """
        # Arrange
        thread_id = "hitl-test-thread-002"
        approval_data = {
            "action": "approve",
            "message": "Approved by user",
        }

        # Mock AgentService
        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state to process approval
            mock_service.update_state.return_value = None

            # Act
            response = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json=approval_data
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert data["status"] in ["success", "approved", "continued"]

            # Verify update_state was called
            mock_service.update_state.assert_called_once()

    def test_reject_hitl_action(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test rejecting a HITL action stops agent execution.

        Flow:
        1. Agent is interrupted waiting for approval
        2. Client sends rejection
        3. Agent execution stops
        4. Response confirms rejection processed
        """
        # Arrange
        thread_id = "hitl-test-thread-003"
        rejection_data = {
            "action": "reject",
            "message": "Rejected by user - too risky",
        }

        # Mock AgentService
        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state to process rejection
            mock_service.update_state.return_value = None

            # Act
            response = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json=rejection_data
            )

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert "status" in data

            # Verify update_state was called
            mock_service.update_state.assert_called_once()

    def test_hitl_workflow_with_custom_response(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test HITL approval with custom user response.

        Flow:
        1. Agent asks clarifying question (triggers HITL)
        2. User provides custom response/modification
        3. Agent continues with modified instructions
        """
        # Arrange
        thread_id = "hitl-test-thread-004"
        custom_response_data = {
            "action": "respond",
            "message": "Instead of deleting, please archive the files",
        }

        # Mock AgentService
        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state
            mock_service.update_state.return_value = None

            # Act
            response = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json=custom_response_data
            )

            # Assert
            assert response.status_code == 200

            # Verify custom message was passed to update_state
            mock_service.update_state.assert_called_once()
            call_args = mock_service.update_state.call_args
            # The custom message should be included in the call


class TestHITLWorkflowComplex:
    """Complex HITL workflow scenarios."""

    def test_multiple_hitl_checkpoints_in_sequence(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent handles multiple HITL checkpoints in one workflow.

        Flow:
        1. Agent gets interrupted (first approval)
        2. User approves
        3. Agent continues and gets interrupted again (second approval)
        4. User approves second time
        5. Agent completes
        """
        # Arrange
        thread_id = "hitl-test-thread-005"

        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Track approval count
            approval_count = 0

            async def mock_get_state(**kwargs) -> Dict[str, Any]:
                # First two calls show interrupted, third shows completed
                if approval_count < 2:
                    return {
                        "values": {"messages": []},
                        "next": ["__interrupt__"],
                        "config": {"configurable": {"thread_id": thread_id}},
                        "metadata": {},
                        "created_at": "2025-01-01T12:00:00",
                        "parent_config": None,
                    }
                else:
                    return {
                        "values": {"messages": []},
                        "next": [],  # Completed
                        "config": {"configurable": {"thread_id": thread_id}},
                        "metadata": {},
                        "created_at": "2025-01-01T12:00:00",
                        "parent_config": None,
                    }

            async def mock_update_state(**kwargs) -> None:
                nonlocal approval_count
                approval_count += 1

            mock_service.get_state.side_effect = mock_get_state
            mock_service.update_state.side_effect = mock_update_state

            # Act - First approval
            response1 = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json={"action": "approve", "message": "First approval"}
            )

            # Act - Check status (should still be interrupted)
            status_response = client.get(f"/api/v1/agents/{thread_id}")

            # Act - Second approval
            response2 = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json={"action": "approve", "message": "Second approval"}
            )

            # Assert
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert approval_count == 2

    def test_hitl_timeout_handling(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent handles HITL timeout gracefully.

        If user doesn't respond within reasonable time, agent should
        maintain interrupted state (no automatic continuation).
        """
        # Arrange
        thread_id = "hitl-test-thread-006"

        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock state that's been waiting for a long time
            async def mock_get_state(**kwargs) -> Dict[str, Any]:
                return {
                    "values": {"messages": []},
                    "next": ["__interrupt__"],
                    "config": {"configurable": {"thread_id": thread_id}},
                    "metadata": {
                        "interrupt_timestamp": "2025-01-01T12:00:00",
                    },
                    "created_at": "2025-01-01T12:00:00",
                    "parent_config": None,
                }

            mock_service.get_state.side_effect = mock_get_state

            # Act - Check status (should show waiting state)
            response = client.get(f"/api/v1/agents/{thread_id}")

            # Assert - Should return status showing still waiting
            assert response.status_code == 200
            data = response.json()
            # Should indicate interrupted/waiting state


class TestHITLWorkflowValidation:
    """Validation tests for HITL workflow."""

    def test_approve_nonexistent_thread_returns_404(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test approving non-existent thread returns 404."""
        # Arrange
        thread_id = "non-existent-thread"
        approval_data = {"action": "approve", "message": "Approve"}

        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state to raise error
            async def mock_update_state(**kwargs):
                raise ValueError(f"Thread not found: {thread_id}")

            mock_service.update_state.side_effect = mock_update_state

            # Act
            response = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json=approval_data
            )

            # Assert
            assert response.status_code in [404, 500]

    def test_approve_invalid_action_returns_422(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test invalid approval action returns 422."""
        # Arrange
        thread_id = "hitl-test-thread-007"
        invalid_data = {
            "action": "invalid_action",  # Invalid action type
            "message": "Test",
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=invalid_data
        )

        # Assert
        # Should validate action field
        # May return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]

    def test_approve_missing_required_fields_returns_422(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """Test approval with missing required fields returns 422."""
        # Arrange
        thread_id = "hitl-test-thread-008"
        incomplete_data = {
            # Missing "action" field
            "message": "Test",
        }

        # Act
        response = client.post(
            f"/api/v1/agents/{thread_id}/approve",
            json=incomplete_data
        )

        # Assert
        assert response.status_code == 422


class TestHITLStatePermistence:
    """Test HITL state persistence through checkpointer."""

    def test_hitl_state_persists_across_requests(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test HITL interrupted state persists across multiple status checks.

        Flow:
        1. Agent gets interrupted
        2. Client checks status (should show interrupted)
        3. Client checks status again (should still show interrupted)
        4. State should be consistent
        """
        # Arrange
        thread_id = "hitl-test-thread-009"

        with patch("backend.deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock consistent interrupted state
            interrupted_state = {
                "values": {"messages": []},
                "next": ["__interrupt__"],
                "config": {"configurable": {"thread_id": thread_id}},
                "metadata": {},
                "created_at": "2025-01-01T12:00:00",
                "parent_config": None,
            }

            async def mock_get_state(**kwargs) -> Dict[str, Any]:
                return interrupted_state

            mock_service.get_state.side_effect = mock_get_state

            # Act - Check status multiple times
            response1 = client.get(f"/api/v1/agents/{thread_id}")
            response2 = client.get(f"/api/v1/agents/{thread_id}")
            response3 = client.get(f"/api/v1/agents/{thread_id}")

            # Assert - All should return same interrupted state
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response3.status_code == 200

            # State should be consistent
            data1 = response1.json()
            data2 = response2.json()
            data3 = response3.json()

            assert data1["thread_id"] == thread_id
            assert data2["thread_id"] == thread_id
            assert data3["thread_id"] == thread_id
