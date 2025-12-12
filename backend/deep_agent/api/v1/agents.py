"""
Agent Management API endpoints for HITL workflows.

Provides REST endpoints for:
- Getting agent run status
- Approving/responding to HITL requests
- Managing agent execution state
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from deep_agent.core.logging import get_logger
from deep_agent.models.agents import (
    AgentRunInfo,
    AgentRunStatus,
    HITLAction,
    HITLApprovalRequest,
    HITLApprovalResponse,
)
from deep_agent.services.agent_service import AgentService

logger = get_logger(__name__)

# Create API router
router = APIRouter()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Constants
HITL_NODE_NAME = "human"  # Node name for human intervention in LangGraph


@router.get(
    "/agents/{thread_id}",
    response_model=AgentRunInfo,
    status_code=status.HTTP_200_OK,
    summary="Get agent run status",
    description="Retrieve current status and state for an agent run by thread ID.",
)
@limiter.limit("30/minute")
async def get_agent_status(request: Request, thread_id: str) -> AgentRunInfo:
    """
    Get current agent run status for a thread.

    Retrieves the persisted state for a conversation thread,
    including execution status, messages, and metadata.

    Args:
        thread_id: Thread ID to get status for.

    Returns:
        AgentRunInfo with current status and metadata.

    Raises:
        HTTPException 404: Thread not found.
        HTTPException 500: Internal server error.

    Example:
        ```bash
        curl http://localhost:8000/api/v1/agents/user-123
        ```

        Response:
        ```json
        {
            "run_id": "checkpoint-abc",
            "thread_id": "user-123",
            "status": "running",
            "started_at": "2025-01-01T12:00:00",
            "completed_at": null
        }
        ```
    """
    logger.info(
        "Getting agent status",
        thread_id=thread_id,
    )

    try:
        # Initialize service
        service = AgentService()

        # Get state from checkpointer
        state = await service.get_state(thread_id)

        # Determine status from state
        if state["next"]:
            # Has next nodes to execute → still running
            agent_status = AgentRunStatus.RUNNING
        else:
            # No next nodes → completed
            agent_status = AgentRunStatus.COMPLETED

        # Extract checkpoint ID as run_id
        run_id = state["config"]["configurable"].get("checkpoint_id", str(uuid.uuid4()))

        # Build response
        run_info = AgentRunInfo(
            run_id=run_id,
            thread_id=thread_id,
            status=agent_status,
            started_at=state.get("created_at") or datetime.now(UTC).isoformat(),
            completed_at=None
            if agent_status == AgentRunStatus.RUNNING
            else state.get("created_at"),
            metadata=state.get("metadata", {}),
        )

        logger.info(
            "Agent status retrieved successfully",
            thread_id=thread_id,
            status=agent_status.value,
        )

        return run_info

    except ValueError as e:
        # Thread not found
        logger.warning(
            "Thread not found",
            thread_id=thread_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread not found: {thread_id}",
        ) from e

    except Exception as e:
        # Internal error
        # Try to extract run_id if state was retrieved
        run_id = None
        try:
            if "state" in locals():
                run_id = state["config"]["configurable"].get("checkpoint_id")
        except Exception:
            pass

        logger.error(
            "Failed to get agent status",
            thread_id=thread_id,
            run_id=run_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent status",
        ) from e


@router.post(
    "/agents/{thread_id}/approve",
    response_model=HITLApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve HITL request",
    description="Approve, respond to, or edit an agent's HITL request.",
)
@limiter.limit("10/minute")
async def approve_hitl_request(
    request: Request,
    thread_id: str,
    approval_request: HITLApprovalRequest,
) -> HITLApprovalResponse:
    """
    Approve HITL (Human-in-the-Loop) request.

    Processes human approval for agent actions. Supports three action types:
    - ACCEPT: Accept agent's proposed action as-is
    - RESPOND: Provide custom text response
    - EDIT: Edit tool parameters before execution

    Args:
        thread_id: Thread ID for the agent run.
        request: Approval request with action and optional data.

    Returns:
        HITLApprovalResponse indicating success and updated status.

    Raises:
        HTTPException 400: No pending HITL request or validation error.
        HTTPException 404: Thread not found.
        HTTPException 422: Invalid request data (validation error).
        HTTPException 500: Internal server error.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/agents/user-123/approve \
          -H "Content-Type: application/json" \
          -d '{
            "run_id": "run-456",
            "thread_id": "user-123",
            "action": "accept"
          }'
        ```

        Response:
        ```json
        {
            "success": true,
            "message": "Action approved and executed",
            "run_id": "run-456",
            "thread_id": "user-123",
            "updated_status": "running"
        }
        ```
    """
    logger.info(
        "Processing HITL approval",
        thread_id=thread_id,
        action=approval_request.action.value,
        run_id=approval_request.run_id,
    )

    # Validate thread_id matches path parameter
    if approval_request.thread_id != thread_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Thread ID mismatch: path={thread_id}, body={approval_request.thread_id}",
        )

    # Validate action-specific requirements
    if approval_request.action == HITLAction.RESPOND and not approval_request.response_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="response_text is required for RESPOND action",
        )

    if approval_request.action == HITLAction.EDIT and not approval_request.tool_edits:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="tool_edits is required for EDIT action",
        )

    try:
        # Initialize service
        service = AgentService()

        # Prepare state update based on action
        state_values: dict[str, Any] = {}

        if approval_request.action == HITLAction.ACCEPT:
            # Accept action as-is
            state_values = {"approved": True}

        elif approval_request.action == HITLAction.RESPOND:
            # Provide custom response
            state_values = {
                "approved": True,
                "custom_response": approval_request.response_text,
            }

        elif approval_request.action == HITLAction.EDIT:
            # Edit tool parameters
            state_values = {
                "approved": True,
                "tool_edits": approval_request.tool_edits,
            }

        # Update state in checkpointer
        await service.update_state(
            thread_id=thread_id,
            values=state_values,
            as_node=HITL_NODE_NAME,  # Attribute update to human
        )

        logger.info(
            "HITL approval processed successfully",
            thread_id=thread_id,
            action=approval_request.action.value,
        )

        # Build response
        response = HITLApprovalResponse(
            success=True,
            message=f"{approval_request.action.value.capitalize()} action processed successfully",
            run_id=approval_request.run_id,
            thread_id=thread_id,
            updated_status=AgentRunStatus.RUNNING,  # Agent resumes after approval
        )

        return response

    except ValueError as e:
        # No pending HITL or thread not found
        error_msg = str(e).lower()

        if "no pending" in error_msg or "not found" in error_msg:
            logger.warning(
                "HITL approval failed - no pending request",
                thread_id=thread_id,
                error=str(e),
            )

            status_code = (
                status.HTTP_404_NOT_FOUND
                if "not found" in error_msg
                else status.HTTP_400_BAD_REQUEST
            )

            raise HTTPException(
                status_code=status_code,
                detail=str(e),
            ) from e

        # Other ValueError
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        # Internal error
        logger.error(
            "Failed to process HITL approval",
            thread_id=thread_id,
            run_id=approval_request.run_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process approval",
        ) from e


@router.post(
    "/agents/{thread_id}/respond",
    response_model=HITLApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Respond to HITL request",
    description="Convenience endpoint for responding to HITL with custom text (wraps /approve with action=respond).",
)
@limiter.limit("10/minute")
async def respond_to_hitl_request(
    request: Request,
    thread_id: str,
    approval_request: HITLApprovalRequest,
) -> HITLApprovalResponse:
    """
    Respond to HITL request with custom text (convenience wrapper).

    This is a convenience endpoint that wraps the /approve endpoint
    specifically for RESPOND actions. It validates that response_text
    is provided and non-empty.

    Args:
        thread_id: Thread ID for the agent run.
        request: Approval request with action=RESPOND and response_text.

    Returns:
        HITLApprovalResponse indicating success.

    Raises:
        HTTPException 400: response_text is empty or missing.
        HTTPException 404: Thread not found.
        HTTPException 422: Invalid request data.
        HTTPException 500: Internal server error.

    Example:
        ```bash
        curl -X POST http://localhost:8000/api/v1/agents/user-123/respond \
          -H "Content-Type: application/json" \
          -d '{
            "run_id": "run-456",
            "thread_id": "user-123",
            "action": "respond",
            "response_text": "Let me provide more context..."
          }'
        ```
    """
    logger.info(
        "Processing HITL response",
        thread_id=thread_id,
        run_id=approval_request.run_id,
    )

    # Validate response_text is provided and non-empty
    if not approval_request.response_text or not approval_request.response_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="response_text cannot be empty",
        )

    # Force action to RESPOND
    approval_request.action = HITLAction.RESPOND

    # Delegate to approve endpoint
    return await approve_hitl_request(request, thread_id, approval_request)
