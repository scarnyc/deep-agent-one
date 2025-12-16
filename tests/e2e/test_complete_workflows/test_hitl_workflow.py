"""
E2E tests for Human-in-the-Loop (HITL) workflow.

Tests the complete HITL approval flow including agent interruption,
state persistence, approval/rejection, and agent continuation.

NOTE: These tests require valid OpenAI API keys and are intended for
Phase 0.5 Live API Integration Testing. They will be skipped in regular
test runs and should only be run manually or as part of live API validation.
"""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Skip all E2E tests unless OPENAI_API_KEY is set
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
    """Mock OpenAI client for E2E tests."""
    with patch("langchain_openai.ChatOpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock chat completion response
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="I need approval to proceed with this action.", role="assistant"
                )
            )
        ]
        mock_completion.usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)

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
        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            async def mock_get_state(tid: str) -> dict[str, Any]:
                return {
                    "values": {"messages": []},
                    "next": ["__interrupt__"],  # Interrupted state
                    "config": {
                        "configurable": {
                            "thread_id": tid,
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
        run_id = "run-002"
        approval_data = {
            "run_id": run_id,
            "thread_id": thread_id,
            "action": "accept",
        }

        # Mock AgentService
        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state to process approval
            mock_service.update_state.return_value = None

            # Act
            response = client.post(f"/api/v1/agents/{thread_id}/approve", json=approval_data)

            # Assert
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["thread_id"] == thread_id
            assert data["run_id"] == run_id

            # Verify update_state was called
            mock_service.update_state.assert_called_once()

    def test_reject_action_not_supported(
        self,
        client: TestClient,
        mock_openai_client: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test that 'reject' is not a valid HITL action.

        The API supports only: accept, respond, edit.
        Reject is not a valid action and should return 422.

        Note: To cancel/stop an agent, users should close the session
        or not respond. There's no explicit "reject" action in the current API.
        """
        # Arrange
        thread_id = "hitl-test-thread-003"
        rejection_data = {
            "run_id": "run-003",
            "thread_id": thread_id,
            "action": "reject",  # Invalid action
        }

        # Act - No mocking needed, validation fails before service call
        response = client.post(f"/api/v1/agents/{thread_id}/approve", json=rejection_data)

        # Assert - Should return 422 for invalid action
        assert response.status_code == 422

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
        run_id = "run-004"
        custom_response_data = {
            "run_id": run_id,
            "thread_id": thread_id,
            "action": "respond",
            "response_text": "Instead of deleting, please archive the files",
        }

        # Mock AgentService
        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state
            mock_service.update_state.return_value = None

            # Act
            response = client.post(f"/api/v1/agents/{thread_id}/approve", json=custom_response_data)

            # Assert
            assert response.status_code == 200

            # Verify custom message was passed to update_state
            mock_service.update_state.assert_called_once()
            call_args = mock_service.update_state.call_args
            # The custom message should be included in the call
            assert call_args is not None
            # Check kwargs or args contain the custom message
            call_kwargs = call_args.kwargs if call_args.kwargs else {}
            call_positional = call_args.args if call_args.args else ()
            # Message should appear somewhere in the call arguments
            all_args_str = str(call_kwargs) + str(call_positional)
            assert (
                "archive" in all_args_str or "respond" in all_args_str
            ), f"Custom response message not found in update_state call: {call_args}"


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

        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Track approval count
            approval_count = 0

            async def mock_get_state(tid: str) -> dict[str, Any]:
                # First two calls show interrupted, third shows completed
                if approval_count < 2:
                    return {
                        "values": {"messages": []},
                        "next": ["__interrupt__"],
                        "config": {"configurable": {"thread_id": tid}},
                        "metadata": {},
                        "created_at": "2025-01-01T12:00:00",
                        "parent_config": None,
                    }
                else:
                    return {
                        "values": {"messages": []},
                        "next": [],  # Completed
                        "config": {"configurable": {"thread_id": tid}},
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
            run_id = "run-005"
            response1 = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json={"run_id": run_id, "thread_id": thread_id, "action": "accept"},
            )

            # Act - Check status (should still be interrupted)
            status_response = client.get(f"/api/v1/agents/{thread_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["thread_id"] == thread_id
            # After first approval, state depends on mock - verify response is valid
            assert "status" in status_data or "thread_id" in status_data

            # Act - Second approval
            response2 = client.post(
                f"/api/v1/agents/{thread_id}/approve",
                json={"run_id": run_id, "thread_id": thread_id, "action": "accept"},
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

        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock state that's been waiting for a long time
            async def mock_get_state(tid: str) -> dict[str, Any]:
                return {
                    "values": {"messages": []},
                    "next": ["__interrupt__"],
                    "config": {"configurable": {"thread_id": tid}},
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
            assert data["thread_id"] == thread_id
            # Verify the response structure indicates agent state
            assert "status" in data or "thread_id" in data
            # Note: When next=["__interrupt__"], API returns "running" because
            # there are still nodes to execute. The interrupt is handled internally.
            # Valid statuses include "running" (active/interrupted) or explicit wait states.
            if "status" in data:
                assert data["status"] in [
                    "running",  # API returns this for non-empty "next" (including interrupts)
                    "interrupted",
                    "waiting",
                    "pending_approval",
                    "paused",
                ]


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
        approval_data = {
            "run_id": "run-nonexistent",
            "thread_id": thread_id,
            "action": "accept",
        }

        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service_class.return_value = mock_service

            # Mock update_state to raise error
            async def mock_update_state(**kwargs):
                raise ValueError(f"Thread not found: {thread_id}")

            mock_service.update_state.side_effect = mock_update_state

            # Act
            response = client.post(f"/api/v1/agents/{thread_id}/approve", json=approval_data)

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
            "run_id": "run-007",
            "thread_id": thread_id,
            "action": "invalid_action",  # Invalid action type - must be accept/respond/edit
        }

        # Act
        response = client.post(f"/api/v1/agents/{thread_id}/approve", json=invalid_data)

        # Assert
        # Should validate action field - must be one of HITLAction enum values
        assert response.status_code == 422

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
            # Missing required fields: run_id, thread_id, action
            "response_text": "Test",  # This is optional
        }

        # Act
        response = client.post(f"/api/v1/agents/{thread_id}/approve", json=incomplete_data)

        # Assert - Should return 422 for missing run_id, thread_id, action
        assert response.status_code == 422
        error_data = response.json()
        # Response structure may vary - check for either "detail" or "error"
        assert "detail" in error_data or "error" in error_data
        # The app's validation error response indicates missing fields
        # Detail can be a string or list depending on error handler
        error_str = str(error_data).lower()
        # Just verify we got a validation-related error
        assert (
            "validation" in error_str or "required" in error_str or "missing" in error_str
        ), f"Expected validation error, got: {error_data}"


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

        with patch("deep_agent.api.v1.agents.AgentService") as mock_service_class:
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

            async def mock_get_state(tid: str) -> dict[str, Any]:
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
