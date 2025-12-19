"""Integration tests for Agent Management Pydantic models.

This module tests business logic, validation rules, and API contracts
for agent run tracking and HITL workflow models.
"""

import pytest
from pydantic import ValidationError

from backend.deep_agent.models.agents import (
    AgentRunInfo,
    AgentRunStatus,
    ErrorResponse,
    HITLAction,
    HITLApprovalRequest,
    HITLApprovalResponse,
)


class TestAgentRunInfoValidation:
    """Test AgentRunInfo model validation rules."""

    def test_run_info_validation_run_id_required(self) -> None:
        """Test that run_id is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(  # type: ignore
                thread_id="user-456",
                status=AgentRunStatus.RUNNING,
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_run_info_validation_thread_id_required(self) -> None:
        """Test that thread_id is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(  # type: ignore
                run_id="run-123",
                status=AgentRunStatus.RUNNING,
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_run_info_validation_status_required(self) -> None:
        """Test that status is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(  # type: ignore
                run_id="run-123",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("status" in str(error["loc"]) for error in errors)

    def test_run_info_validation_empty_run_id(self) -> None:
        """Test that empty run_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(
                run_id="",
                thread_id="user-456",
                status=AgentRunStatus.RUNNING,
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)
        assert any("empty" in str(error["msg"]).lower() for error in errors)

    def test_run_info_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(
                run_id="run-123",
                thread_id="",
                status=AgentRunStatus.RUNNING,
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)
        assert any("empty" in str(error["msg"]).lower() for error in errors)

    def test_run_info_validation_whitespace_run_id(self) -> None:
        """Test that whitespace-only run_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(
                run_id="   ",
                thread_id="user-456",
                status=AgentRunStatus.RUNNING,
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_run_info_validation_whitespace_thread_id(self) -> None:
        """Test that whitespace-only thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            AgentRunInfo(
                run_id="run-123",
                thread_id="   ",
                status=AgentRunStatus.RUNNING,
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_run_info_all_statuses(self) -> None:
        """Test run info accepts all valid status types."""
        statuses = [
            AgentRunStatus.RUNNING,
            AgentRunStatus.COMPLETED,
            AgentRunStatus.ERROR,
            AgentRunStatus.INTERRUPTED,
        ]

        for status in statuses:
            run_info = AgentRunInfo(
                run_id="run-123",
                thread_id="user-456",
                status=status,
            )
            assert run_info.status == status

    def test_run_info_with_error(self) -> None:
        """Test run info accepts error message with ERROR status."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.ERROR,
            error="Connection timeout",
        )
        assert run_info.error == "Connection timeout"
        assert run_info.status == AgentRunStatus.ERROR

    def test_run_info_with_metadata(self) -> None:
        """Test run info accepts optional metadata."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
            metadata={"user_id": "12345", "source": "web"},
        )
        assert run_info.metadata is not None
        assert run_info.metadata["user_id"] == "12345"
        assert run_info.metadata["source"] == "web"

    def test_run_info_with_trace_id(self) -> None:
        """Test run info accepts optional trace_id for debugging."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
            trace_id="trace-abc-456",
        )
        assert run_info.trace_id == "trace-abc-456"


class TestHITLApprovalRequestValidation:
    """Test HITLApprovalRequest model validation rules."""

    def test_approval_request_validation_run_id_required(self) -> None:
        """Test that run_id is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(  # type: ignore
                thread_id="user-456",
                action=HITLAction.ACCEPT,
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_approval_request_validation_thread_id_required(self) -> None:
        """Test that thread_id is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(  # type: ignore
                run_id="run-123",
                action=HITLAction.ACCEPT,
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_approval_request_validation_action_required(self) -> None:
        """Test that action is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(  # type: ignore
                run_id="run-123",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("action" in str(error["loc"]) for error in errors)

    def test_approval_request_validation_empty_run_id(self) -> None:
        """Test that empty run_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(
                run_id="",
                thread_id="user-456",
                action=HITLAction.ACCEPT,
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_approval_request_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(
                run_id="run-123",
                thread_id="",
                action=HITLAction.ACCEPT,
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_approval_request_validation_whitespace_run_id(self) -> None:
        """Test that whitespace-only run_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(
                run_id="   ",
                thread_id="user-456",
                action=HITLAction.ACCEPT,
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_approval_request_validation_whitespace_thread_id(self) -> None:
        """Test that whitespace-only thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalRequest(
                run_id="run-123",
                thread_id="   ",
                action=HITLAction.ACCEPT,
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_approval_request_all_actions(self) -> None:
        """Test approval request accepts all action types."""
        actions = [HITLAction.ACCEPT, HITLAction.RESPOND, HITLAction.EDIT]

        for action in actions:
            request = HITLApprovalRequest(
                run_id="run-123",
                thread_id="user-456",
                action=action,
            )
            assert request.action == action

    def test_approval_request_respond_with_long_text(self) -> None:
        """Test RESPOND action accepts long response text."""
        long_text = "A" * 5000
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.RESPOND,
            response_text=long_text,
        )
        assert len(request.response_text or "") == 5000

    def test_approval_request_edit_with_complex_edits(self) -> None:
        """Test EDIT action accepts complex tool edits."""
        complex_edits = {
            "tool_name": "updated_tool",
            "args": {"param1": "value1", "param2": {"nested": "value"}},
            "metadata": {"reason": "optimization"},
        }
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.EDIT,
            tool_edits=complex_edits,
        )
        assert request.tool_edits is not None
        assert request.tool_edits["args"]["param2"]["nested"] == "value"


class TestHITLApprovalResponseValidation:
    """Test HITLApprovalResponse model validation rules."""

    def test_approval_response_validation_success_required(self) -> None:
        """Test that success is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(  # type: ignore
                message="Test message",
                run_id="run-123",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("success" in str(error["loc"]) for error in errors)

    def test_approval_response_validation_message_required(self) -> None:
        """Test that message is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(  # type: ignore
                success=True,
                run_id="run-123",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("message" in str(error["loc"]) for error in errors)

    def test_approval_response_validation_run_id_required(self) -> None:
        """Test that run_id is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(  # type: ignore
                success=True,
                message="Test message",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_approval_response_validation_thread_id_required(self) -> None:
        """Test that thread_id is required (API contract)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(  # type: ignore
                success=True,
                message="Test message",
                run_id="run-123",
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_approval_response_validation_empty_message(self) -> None:
        """Test that empty message is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(
                success=True,
                message="",
                run_id="run-123",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("message" in str(error["loc"]) for error in errors)
        assert any("empty" in str(error["msg"]).lower() for error in errors)

    def test_approval_response_validation_whitespace_message(self) -> None:
        """Test that whitespace-only message is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(
                success=True,
                message="   ",
                run_id="run-123",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("message" in str(error["loc"]) for error in errors)

    def test_approval_response_validation_empty_run_id(self) -> None:
        """Test that empty run_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(
                success=True,
                message="Test message",
                run_id="",
                thread_id="user-456",
            )

        errors = exc_info.value.errors()
        assert any("run_id" in str(error["loc"]) for error in errors)

    def test_approval_response_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is rejected (business rule)."""
        with pytest.raises(ValidationError) as exc_info:
            HITLApprovalResponse(
                success=True,
                message="Test message",
                run_id="run-123",
                thread_id="",
            )

        errors = exc_info.value.errors()
        assert any("thread_id" in str(error["loc"]) for error in errors)

    def test_approval_response_with_updated_status(self) -> None:
        """Test approval response accepts optional updated status."""
        response = HITLApprovalResponse(
            success=True,
            message="Action completed",
            run_id="run-123",
            thread_id="user-456",
            updated_status=AgentRunStatus.COMPLETED,
        )

        assert response.updated_status == AgentRunStatus.COMPLETED

    def test_approval_response_all_statuses(self) -> None:
        """Test approval response accepts all status types."""
        statuses = [
            AgentRunStatus.RUNNING,
            AgentRunStatus.COMPLETED,
            AgentRunStatus.ERROR,
            AgentRunStatus.INTERRUPTED,
        ]

        for status in statuses:
            response = HITLApprovalResponse(
                success=True,
                message="Status updated",
                run_id="run-123",
                thread_id="user-456",
                updated_status=status,
            )
            assert response.updated_status == status


class TestErrorResponseValidation:
    """Test ErrorResponse model validation rules."""

    def test_error_response_with_all_fields(self) -> None:
        """Test error response accepts all debugging identifiers."""
        error = ErrorResponse(
            error="Agent execution failed",
            detail="Connection timeout after 30 seconds",
            thread_id="user-123",
            trace_id="trace-abc-456",
            run_id="run-def-789",
            request_id="req-ghi-012",
        )

        assert error.error == "Agent execution failed"
        assert error.detail == "Connection timeout after 30 seconds"
        assert error.thread_id == "user-123"
        assert error.trace_id == "trace-abc-456"
        assert error.run_id == "run-def-789"
        assert error.request_id == "req-ghi-012"

    def test_error_response_minimal(self) -> None:
        """Test error response with only required error field."""
        error = ErrorResponse(error="Something went wrong")
        assert error.error == "Something went wrong"
        assert error.detail is None
        assert error.thread_id is None
        assert error.trace_id is None
        assert error.run_id is None
        assert error.request_id is None
