"""Agent Management Pydantic models for run tracking and HITL workflows."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


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
        default_factory=datetime.utcnow,
        description="When the run started",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the run completed",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is ERROR",
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the run",
    )

    @field_validator("run_id", "thread_id", mode="before")
    @classmethod
    def strip_and_validate_string(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        if not isinstance(v, str):
            raise ValueError("Value must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Value cannot be empty or whitespace-only")

        return stripped

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
    response_text: Optional[str] = Field(
        default=None,
        description="Text response (for RESPOND action)",
    )
    tool_edits: Optional[dict[str, Any]] = Field(
        default=None,
        description="Tool parameter edits (for EDIT action)",
    )

    @field_validator("run_id", "thread_id", mode="before")
    @classmethod
    def strip_and_validate_string(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        if not isinstance(v, str):
            raise ValueError("Value must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Value cannot be empty or whitespace-only")

        return stripped

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
    updated_status: Optional[AgentRunStatus] = Field(
        default=None,
        description="New status of the run (if changed)",
    )

    @field_validator("message", "run_id", "thread_id", mode="before")
    @classmethod
    def strip_and_validate_string(cls, v: Any) -> str:
        """Strip whitespace and validate string is not empty."""
        if not isinstance(v, str):
            raise ValueError("Value must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Value cannot be empty or whitespace-only")

        return stripped

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
