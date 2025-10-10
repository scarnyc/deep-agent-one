"""Tests for Agent Management Pydantic models."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.deep_agent.models.agents import (
    AgentRunInfo,
    AgentRunStatus,
    HITLAction,
    HITLApprovalRequest,
    HITLApprovalResponse,
)


class TestAgentRunStatus:
    """Test AgentRunStatus enum."""

    def test_agent_run_status_values(self) -> None:
        """Test all agent run status enum values."""
        assert AgentRunStatus.RUNNING == "running"
        assert AgentRunStatus.COMPLETED == "completed"
        assert AgentRunStatus.ERROR == "error"
        assert AgentRunStatus.INTERRUPTED == "interrupted"

    def test_agent_run_status_from_string(self) -> None:
        """Test creating AgentRunStatus from string."""
        assert AgentRunStatus("running") == AgentRunStatus.RUNNING
        assert AgentRunStatus("completed") == AgentRunStatus.COMPLETED
        assert AgentRunStatus("error") == AgentRunStatus.ERROR
        assert AgentRunStatus("interrupted") == AgentRunStatus.INTERRUPTED


class TestHITLAction:
    """Test HITLAction enum."""

    def test_hitl_action_values(self) -> None:
        """Test all HITL action enum values."""
        assert HITLAction.ACCEPT == "accept"
        assert HITLAction.RESPOND == "respond"
        assert HITLAction.EDIT == "edit"

    def test_hitl_action_from_string(self) -> None:
        """Test creating HITLAction from string."""
        assert HITLAction("accept") == HITLAction.ACCEPT
        assert HITLAction("respond") == HITLAction.RESPOND
        assert HITLAction("edit") == HITLAction.EDIT


class TestAgentRunInfo:
    """Test AgentRunInfo model."""

    def test_valid_run_info(self) -> None:
        """Test creating valid agent run info."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
        )

        assert run_info.run_id == "run-123"
        assert run_info.thread_id == "user-456"
        assert run_info.status == AgentRunStatus.RUNNING
        assert isinstance(run_info.started_at, datetime)
        assert run_info.completed_at is None
        assert run_info.error is None
        assert run_info.metadata is None

    def test_run_info_validation_run_id_required(self) -> None:
        """Test that run_id is required."""
        with pytest.raises(ValidationError):
            AgentRunInfo(  # type: ignore
                thread_id="user-456",
                status=AgentRunStatus.RUNNING,
            )

    def test_run_info_validation_thread_id_required(self) -> None:
        """Test that thread_id is required."""
        with pytest.raises(ValidationError):
            AgentRunInfo(  # type: ignore
                run_id="run-123",
                status=AgentRunStatus.RUNNING,
            )

    def test_run_info_validation_status_required(self) -> None:
        """Test that status is required."""
        with pytest.raises(ValidationError):
            AgentRunInfo(  # type: ignore
                run_id="run-123",
                thread_id="user-456",
            )

    def test_run_info_validation_empty_run_id(self) -> None:
        """Test that empty run_id is not allowed."""
        with pytest.raises(ValidationError):
            AgentRunInfo(
                run_id="",
                thread_id="user-456",
                status=AgentRunStatus.RUNNING,
            )

    def test_run_info_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is not allowed."""
        with pytest.raises(ValidationError):
            AgentRunInfo(
                run_id="run-123",
                thread_id="",
                status=AgentRunStatus.RUNNING,
            )

    def test_run_info_validation_whitespace_run_id(self) -> None:
        """Test that whitespace-only run_id is not allowed."""
        with pytest.raises(ValidationError):
            AgentRunInfo(
                run_id="   ",
                thread_id="user-456",
                status=AgentRunStatus.RUNNING,
            )

    def test_run_info_validation_whitespace_thread_id(self) -> None:
        """Test that whitespace-only thread_id is not allowed."""
        with pytest.raises(ValidationError):
            AgentRunInfo(
                run_id="run-123",
                thread_id="   ",
                status=AgentRunStatus.RUNNING,
            )

    def test_run_info_started_at_auto_generated(self) -> None:
        """Test that started_at is automatically generated."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
        )
        assert run_info.started_at is not None
        assert isinstance(run_info.started_at, datetime)

    def test_run_info_with_custom_started_at(self) -> None:
        """Test run info with custom started_at timestamp."""
        custom_time = datetime(2025, 1, 1, 12, 0, 0)
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
            started_at=custom_time,
        )
        assert run_info.started_at == custom_time

    def test_run_info_all_statuses(self) -> None:
        """Test run info with all status types."""
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

    def test_run_info_with_completed_at(self) -> None:
        """Test run info with completion timestamp."""
        completed_time = datetime(2025, 1, 1, 12, 30, 0)
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.COMPLETED,
            completed_at=completed_time,
        )
        assert run_info.completed_at == completed_time

    def test_run_info_with_error(self) -> None:
        """Test run info with error message."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.ERROR,
            error="Connection timeout",
        )
        assert run_info.error == "Connection timeout"
        assert run_info.status == AgentRunStatus.ERROR

    def test_run_info_with_metadata(self) -> None:
        """Test run info with metadata."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
            metadata={"user_id": "12345", "source": "web"},
        )
        assert run_info.metadata is not None
        assert run_info.metadata["user_id"] == "12345"
        assert run_info.metadata["source"] == "web"

    def test_run_info_serialization(self) -> None:
        """Test AgentRunInfo serialization to dict."""
        run_info = AgentRunInfo(
            run_id="run-123",
            thread_id="user-456",
            status=AgentRunStatus.RUNNING,
        )
        data = run_info.model_dump()

        assert data["run_id"] == "run-123"
        assert data["thread_id"] == "user-456"
        assert data["status"] == "running"
        assert "started_at" in data

    def test_run_info_deserialization(self) -> None:
        """Test AgentRunInfo deserialization from dict."""
        data = {
            "run_id": "run-456",
            "thread_id": "user-789",
            "status": "completed",
            "started_at": "2025-01-01T12:00:00",
            "completed_at": "2025-01-01T12:30:00",
        }
        run_info = AgentRunInfo(**data)

        assert run_info.run_id == "run-456"
        assert run_info.thread_id == "user-789"
        assert run_info.status == AgentRunStatus.COMPLETED


class TestHITLApprovalRequest:
    """Test HITLApprovalRequest model."""

    def test_valid_approval_request_accept(self) -> None:
        """Test creating valid approval request with ACCEPT action."""
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.ACCEPT,
        )

        assert request.run_id == "run-123"
        assert request.thread_id == "user-456"
        assert request.action == HITLAction.ACCEPT
        assert request.response_text is None
        assert request.tool_edits is None

    def test_valid_approval_request_respond(self) -> None:
        """Test creating valid approval request with RESPOND action."""
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.RESPOND,
            response_text="Please use a different approach",
        )

        assert request.action == HITLAction.RESPOND
        assert request.response_text == "Please use a different approach"

    def test_valid_approval_request_edit(self) -> None:
        """Test creating valid approval request with EDIT action."""
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.EDIT,
            tool_edits={"tool_name": "new_tool", "args": {"param": "value"}},
        )

        assert request.action == HITLAction.EDIT
        assert request.tool_edits is not None
        assert request.tool_edits["tool_name"] == "new_tool"

    def test_approval_request_validation_run_id_required(self) -> None:
        """Test that run_id is required."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(  # type: ignore
                thread_id="user-456",
                action=HITLAction.ACCEPT,
            )

    def test_approval_request_validation_thread_id_required(self) -> None:
        """Test that thread_id is required."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(  # type: ignore
                run_id="run-123",
                action=HITLAction.ACCEPT,
            )

    def test_approval_request_validation_action_required(self) -> None:
        """Test that action is required."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(  # type: ignore
                run_id="run-123",
                thread_id="user-456",
            )

    def test_approval_request_validation_empty_run_id(self) -> None:
        """Test that empty run_id is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(
                run_id="",
                thread_id="user-456",
                action=HITLAction.ACCEPT,
            )

    def test_approval_request_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(
                run_id="run-123",
                thread_id="",
                action=HITLAction.ACCEPT,
            )

    def test_approval_request_validation_whitespace_run_id(self) -> None:
        """Test that whitespace-only run_id is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(
                run_id="   ",
                thread_id="user-456",
                action=HITLAction.ACCEPT,
            )

    def test_approval_request_validation_whitespace_thread_id(self) -> None:
        """Test that whitespace-only thread_id is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalRequest(
                run_id="run-123",
                thread_id="   ",
                action=HITLAction.ACCEPT,
            )

    def test_approval_request_all_actions(self) -> None:
        """Test approval request with all action types."""
        actions = [HITLAction.ACCEPT, HITLAction.RESPOND, HITLAction.EDIT]

        for action in actions:
            request = HITLApprovalRequest(
                run_id="run-123",
                thread_id="user-456",
                action=action,
            )
            assert request.action == action

    def test_approval_request_respond_with_long_text(self) -> None:
        """Test RESPOND action with long response text."""
        long_text = "A" * 5000
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.RESPOND,
            response_text=long_text,
        )
        assert len(request.response_text or "") == 5000

    def test_approval_request_edit_with_complex_edits(self) -> None:
        """Test EDIT action with complex tool edits."""
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

    def test_approval_request_serialization(self) -> None:
        """Test HITLApprovalRequest serialization to dict."""
        request = HITLApprovalRequest(
            run_id="run-123",
            thread_id="user-456",
            action=HITLAction.ACCEPT,
        )
        data = request.model_dump()

        assert data["run_id"] == "run-123"
        assert data["thread_id"] == "user-456"
        assert data["action"] == "accept"

    def test_approval_request_deserialization(self) -> None:
        """Test HITLApprovalRequest deserialization from dict."""
        data = {
            "run_id": "run-456",
            "thread_id": "user-789",
            "action": "respond",
            "response_text": "Please try again",
        }
        request = HITLApprovalRequest(**data)

        assert request.run_id == "run-456"
        assert request.thread_id == "user-789"
        assert request.action == HITLAction.RESPOND
        assert request.response_text == "Please try again"


class TestHITLApprovalResponse:
    """Test HITLApprovalResponse model."""

    def test_valid_approval_response_success(self) -> None:
        """Test creating valid approval response (success)."""
        response = HITLApprovalResponse(
            success=True,
            message="Action approved and executed",
            run_id="run-123",
            thread_id="user-456",
        )

        assert response.success is True
        assert response.message == "Action approved and executed"
        assert response.run_id == "run-123"
        assert response.thread_id == "user-456"
        assert response.updated_status is None

    def test_valid_approval_response_failure(self) -> None:
        """Test creating valid approval response (failure)."""
        response = HITLApprovalResponse(
            success=False,
            message="Invalid action parameters",
            run_id="run-123",
            thread_id="user-456",
        )

        assert response.success is False
        assert response.message == "Invalid action parameters"

    def test_approval_response_validation_success_required(self) -> None:
        """Test that success is required."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(  # type: ignore
                message="Test message",
                run_id="run-123",
                thread_id="user-456",
            )

    def test_approval_response_validation_message_required(self) -> None:
        """Test that message is required."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(  # type: ignore
                success=True,
                run_id="run-123",
                thread_id="user-456",
            )

    def test_approval_response_validation_run_id_required(self) -> None:
        """Test that run_id is required."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(  # type: ignore
                success=True,
                message="Test message",
                thread_id="user-456",
            )

    def test_approval_response_validation_thread_id_required(self) -> None:
        """Test that thread_id is required."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(  # type: ignore
                success=True,
                message="Test message",
                run_id="run-123",
            )

    def test_approval_response_validation_empty_message(self) -> None:
        """Test that empty message is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(
                success=True,
                message="",
                run_id="run-123",
                thread_id="user-456",
            )

    def test_approval_response_validation_whitespace_message(self) -> None:
        """Test that whitespace-only message is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(
                success=True,
                message="   ",
                run_id="run-123",
                thread_id="user-456",
            )

    def test_approval_response_validation_empty_run_id(self) -> None:
        """Test that empty run_id is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(
                success=True,
                message="Test message",
                run_id="",
                thread_id="user-456",
            )

    def test_approval_response_validation_empty_thread_id(self) -> None:
        """Test that empty thread_id is not allowed."""
        with pytest.raises(ValidationError):
            HITLApprovalResponse(
                success=True,
                message="Test message",
                run_id="run-123",
                thread_id="",
            )

    def test_approval_response_with_updated_status(self) -> None:
        """Test approval response with updated status."""
        response = HITLApprovalResponse(
            success=True,
            message="Action completed",
            run_id="run-123",
            thread_id="user-456",
            updated_status=AgentRunStatus.COMPLETED,
        )

        assert response.updated_status == AgentRunStatus.COMPLETED

    def test_approval_response_all_statuses(self) -> None:
        """Test approval response with all status types."""
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

    def test_approval_response_serialization(self) -> None:
        """Test HITLApprovalResponse serialization to dict."""
        response = HITLApprovalResponse(
            success=True,
            message="Action approved",
            run_id="run-123",
            thread_id="user-456",
        )
        data = response.model_dump()

        assert data["success"] is True
        assert data["message"] == "Action approved"
        assert data["run_id"] == "run-123"
        assert data["thread_id"] == "user-456"

    def test_approval_response_deserialization(self) -> None:
        """Test HITLApprovalResponse deserialization from dict."""
        data = {
            "success": True,
            "message": "Execution complete",
            "run_id": "run-456",
            "thread_id": "user-789",
            "updated_status": "completed",
        }
        response = HITLApprovalResponse(**data)

        assert response.success is True
        assert response.message == "Execution complete"
        assert response.run_id == "run-456"
        assert response.thread_id == "user-789"
        assert response.updated_status == AgentRunStatus.COMPLETED
