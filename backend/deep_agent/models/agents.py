"""
Agent Management Pydantic models for run tracking and HITL workflows.

This module provides models for:
- Error responses with debugging identifiers (ErrorResponse)
- Agent run status tracking (AgentRunInfo, AgentRunStatus)
- Human-in-the-loop (HITL) approval workflows (HITLApprovalRequest, HITLApprovalResponse, HITLAction)

Models:
    ErrorResponse: Generic error response with trace_id, run_id, request_id for debugging
    AgentRunStatus: Enum for run states (running, completed, error, interrupted)
    HITLAction: Enum for human intervention types (accept, respond, edit)
    AgentRunInfo: Tracks agent execution state, timing, and metadata
    HITLApprovalRequest: Request model for human approval/rejection/editing
    HITLApprovalResponse: Response model indicating approval action result

Validation Features:
    - Non-empty string validation with whitespace stripping
    - Auto-generated UTC timestamps for run start times
    - Optional trace_id/run_id linking for debugging with LangSmith/LangGraph

Example:
    >>> from deep_agent.models.agents import AgentRunInfo, AgentRunStatus
    >>> run_info = AgentRunInfo(
    ...     run_id="run-abc-123",
    ...     thread_id="user-456",
    ...     status=AgentRunStatus.RUNNING
    ... )
    >>> print(run_info.status, run_info.started_at)
    AgentRunStatus.RUNNING 2025-01-01 12:00:00+00:00

HITL Workflow Example:
    >>> from deep_agent.models.agents import HITLApprovalRequest, HITLAction
    >>> approval = HITLApprovalRequest(
    ...     run_id="run-abc-123",
    ...     thread_id="user-456",
    ...     action=HITLAction.ACCEPT
    ... )
    >>> # Send to agent service for processing
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _strip_and_validate_string(v: Any) -> str:
    """
    Shared validator for string fields - strips whitespace and validates non-empty.

    Used by AgentRunInfo, HITLApprovalRequest, and HITLApprovalResponse models
    to ensure consistent validation of run_id, thread_id, and message fields.

    Args:
        v: Input value to validate (must be a string)

    Returns:
        str: Stripped string value

    Raises:
        ValueError: If input is not a string or is empty/whitespace-only
    """
    if not isinstance(v, str):
        raise ValueError("Value must be a string")

    stripped = v.strip()
    if not stripped:
        raise ValueError("Value cannot be empty or whitespace-only")

    return stripped


class ErrorResponse(BaseModel):
    """
    Generic error response model for API endpoints.

    Provides consistent error structure across all endpoints with debugging identifiers.

    Attributes:
        error: Human-readable error message
        detail: Optional detailed error information
        thread_id: Optional conversation thread identifier
        trace_id: Optional LangSmith trace ID for debugging
        run_id: Optional LangGraph checkpoint/run ID
        request_id: Optional request identifier (for WebSocket/async requests)

    Example:
        >>> error = ErrorResponse(
        ...     error="Agent execution failed",
        ...     thread_id="user-123",
        ...     trace_id="trace-abc-456"
        ... )
        >>> print(error.error, error.trace_id)
        Agent execution failed trace-abc-456
    """

    error: str = Field(
        min_length=1,
        description="Human-readable error message",
    )
    detail: str | None = Field(
        default=None,
        description="Optional detailed error information",
    )
    thread_id: str | None = Field(
        default=None,
        description="Conversation thread identifier",
    )
    trace_id: str | None = Field(
        default=None,
        description="LangSmith trace ID for debugging (links to execution trace)",
    )
    run_id: str | None = Field(
        default=None,
        description="LangGraph checkpoint/run ID for state inspection",
    )
    request_id: str | None = Field(
        default=None,
        description="Request identifier (for WebSocket/async requests)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Agent execution failed",
                "detail": "Connection timeout after 30 seconds",
                "thread_id": "user-123",
                "trace_id": "trace-abc-456",
                "run_id": "run-def-789",
                "request_id": "req-ghi-012",
            }
        }
    }


class AgentRunStatus(str, Enum):
    """
    Agent run status types.

    Indicates the current state of an agent execution.
    """

    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    INTERRUPTED = "interrupted"


class HITLAction(str, Enum):
    """
    Human-in-the-loop action types.

    Defines the type of human intervention during agent execution.
    """

    ACCEPT = "accept"
    RESPOND = "respond"
    EDIT = "edit"


class AgentRunInfo(BaseModel):
    """
    Information about an agent run.

    Tracks the state, timing, and metadata of an agent execution.

    Attributes:
        run_id: Unique identifier for the agent run
        thread_id: Thread/conversation identifier
        status: Current status of the run
        started_at: When the run started (auto-generated if not provided)
        completed_at: When the run completed (None if still running)
        error: Error message if status is ERROR
        metadata: Optional metadata about the run

    Example:
        >>> run_info = AgentRunInfo(
        ...     run_id="run-123",
        ...     thread_id="user-456",
        ...     status=AgentRunStatus.RUNNING
        ... )
        >>> print(run_info.status, run_info.run_id)
        AgentRunStatus.RUNNING run-123
    """

    run_id: str = Field(
        min_length=1,
        description="Unique identifier for the agent run",
    )
    thread_id: str = Field(
        min_length=1,
        description="Thread/conversation identifier",
    )
    status: AgentRunStatus = Field(
        description="Current status of the run",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the run started (UTC)",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="When the run completed",
    )
    error: str | None = Field(
        default=None,
        description="Error message if status is ERROR",
    )
    trace_id: str | None = Field(
        default=None,
        description="LangSmith trace ID for debugging (links to execution trace)",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata about the run",
    )

    @field_validator("run_id", "thread_id", mode="before")
    @classmethod
    def validate_string_fields(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        return _strip_and_validate_string(v)

    model_config = {
        "json_schema_extra": {
            "example": {
                "run_id": "run-123",
                "thread_id": "user-456",
                "status": "running",
                "started_at": "2025-01-01T12:00:00",
            }
        }
    }


class HITLApprovalRequest(BaseModel):
    """
    Request model for HITL approval actions.

    Used when a human approves, rejects, or edits an agent's proposed action.

    Attributes:
        run_id: Unique identifier for the agent run
        thread_id: Thread/conversation identifier
        action: Type of approval action (accept/respond/edit)
        response_text: Text response (required for RESPOND action)
        tool_edits: Tool parameter edits (required for EDIT action)

    Example:
        >>> request = HITLApprovalRequest(
        ...     run_id="run-123",
        ...     thread_id="user-456",
        ...     action=HITLAction.ACCEPT
        ... )
        >>> print(request.action)
        HITLAction.ACCEPT
    """

    run_id: str = Field(
        min_length=1,
        description="Unique identifier for the agent run",
    )
    thread_id: str = Field(
        min_length=1,
        description="Thread/conversation identifier",
    )
    action: HITLAction = Field(
        description="Type of approval action",
    )
    response_text: str | None = Field(
        default=None,
        description="Text response (for RESPOND action)",
    )
    tool_edits: dict[str, Any] | None = Field(
        default=None,
        description="Tool parameter edits (for EDIT action)",
    )

    @field_validator("run_id", "thread_id", mode="before")
    @classmethod
    def validate_string_fields(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        return _strip_and_validate_string(v)

    model_config = {
        "json_schema_extra": {
            "example": {
                "run_id": "run-123",
                "thread_id": "user-456",
                "action": "accept",
            }
        }
    }


class HITLApprovalResponse(BaseModel):
    """
    Response model for HITL approval actions.

    Indicates whether the approval action was successfully processed.

    Attributes:
        success: Whether the action was successful
        message: Human-readable message about the result
        run_id: Unique identifier for the agent run
        thread_id: Thread/conversation identifier
        updated_status: New status of the run (if changed)

    Example:
        >>> response = HITLApprovalResponse(
        ...     success=True,
        ...     message="Action approved and executed",
        ...     run_id="run-123",
        ...     thread_id="user-456"
        ... )
        >>> print(response.success, response.message)
        True Action approved and executed
    """

    success: bool = Field(
        description="Whether the action was successful",
    )
    message: str = Field(
        min_length=1,
        description="Human-readable message about the result",
    )
    run_id: str = Field(
        min_length=1,
        description="Unique identifier for the agent run",
    )
    thread_id: str = Field(
        min_length=1,
        description="Thread/conversation identifier",
    )
    updated_status: AgentRunStatus | None = Field(
        default=None,
        description="New status of the run (if changed)",
    )

    @field_validator("message", "run_id", "thread_id", mode="before")
    @classmethod
    def validate_string_fields(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        return _strip_and_validate_string(v)

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Action approved and executed",
                "run_id": "run-123",
                "thread_id": "user-456",
            }
        }
    }
