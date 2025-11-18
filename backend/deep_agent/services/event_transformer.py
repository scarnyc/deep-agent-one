"""
Event Transformer for LangGraph → UI Event Mapping.

Transforms LangGraph event format to match frontend UI component expectations.
This decouples the frontend from LangGraph's event schema, allowing independent evolution.

UI Components Expectations:
- ProgressTracker: Expects `on_step` events with {id, name, status, started_at, completed_at}
- ToolCallDisplay: Expects `on_tool_call` events with {id, name, args, result, status, started_at, completed_at}
"""

from datetime import datetime
from typing import Any
import uuid


class EventTransformer:
    """
    Transform LangGraph events to UI-compatible format.

    Maps LangGraph's event schema to the format expected by frontend UI components:
    - on_tool_start → on_tool_call (status="running")
    - on_tool_end → on_tool_call (status="completed")
    - on_chain_start → on_step (status="running")
    - on_chain_end → on_step (status="completed")

    All other events pass through unchanged.
    """

    def transform(self, langgraph_event: dict[str, Any]) -> dict[str, Any]:
        """
        Transform a LangGraph event to UI format.

        Args:
            langgraph_event: Raw event from LangGraph's astream_events() API

        Returns:
            Transformed event matching UI component expectations

        Example:
            >>> transformer = EventTransformer()
            >>> event = {"event": "on_tool_start", "run_id": "123", "name": "web_search", "data": {"input": {"query": "test"}}}
            >>> transformed = transformer.transform(event)
            >>> transformed["event"]
            'on_tool_call'
            >>> transformed["data"]["status"]
            'running'
        """
        event_type = langgraph_event.get("event")

        # Transform tool events → on_tool_call
        if event_type == "on_tool_start":
            return self._transform_tool_start(langgraph_event)
        elif event_type == "on_tool_end":
            return self._transform_tool_end(langgraph_event)

        # Transform chain events → on_step
        elif event_type == "on_chain_start":
            return self._transform_chain_start(langgraph_event)
        elif event_type == "on_chain_end":
            return self._transform_chain_end(langgraph_event)

        # Transform chat model completion → on_message_complete
        elif event_type == "on_chat_model_end":
            return self._transform_chat_model_end(langgraph_event)

        # Pass through all other events unchanged
        # (on_chat_model_stream, heartbeat, on_error, etc.)
        return langgraph_event

    def _transform_tool_start(self, event: dict[str, Any]) -> dict[str, Any]:
        """Transform on_tool_start → on_tool_call (running)."""
        # Use run_id as unique identifier - each tool execution gets its own run_id
        # This ID will be used to match on_tool_end events for updates
        tool_id = event.get("run_id", f"tool_{uuid.uuid4().hex[:8]}")

        return {
            "event": "on_tool_call",
            "data": {
                "id": tool_id,
                "name": event.get("name", "unknown_tool"),
                "args": event.get("data", {}).get("input", {}),
                "result": None,  # Not available yet
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None,
            },
            "metadata": event.get("metadata", {}),
        }

    def _transform_tool_end(self, event: dict[str, Any]) -> dict[str, Any]:
        """Transform on_tool_end → on_tool_call (completed)."""
        # Use same run_id as on_tool_start so frontend can update the existing tool call
        tool_id = event.get("run_id", f"tool_{uuid.uuid4().hex[:8]}")

        return {
            "event": "on_tool_call",
            "data": {
                "id": tool_id,
                "name": event.get("name", "unknown_tool"),
                "args": event.get("data", {}).get("input", {}),
                "result": event.get("data", {}).get("output"),
                "status": "completed",
                "started_at": None,  # Not available in end event
                "completed_at": datetime.utcnow().isoformat(),
                "error": None,
            },
            "metadata": event.get("metadata", {}),
        }

    def _transform_chain_start(self, event: dict[str, Any]) -> dict[str, Any]:
        """Transform on_chain_start → on_step (running)."""
        # Use run_id as unique identifier - each chain execution gets its own run_id
        # This ID will be used to match on_chain_end events for updates
        step_id = event.get("run_id", f"step_{uuid.uuid4().hex[:8]}")

        return {
            "event": "on_step",
            "data": {
                "id": step_id,
                "name": event.get("name", "Processing"),
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "metadata": event.get("data", {}),
            },
            "metadata": event.get("metadata", {}),
        }

    def _transform_chain_end(self, event: dict[str, Any]) -> dict[str, Any]:
        """Transform on_chain_end → on_step (completed)."""
        # Use same run_id as on_chain_start so frontend can update the existing step
        step_id = event.get("run_id", f"step_{uuid.uuid4().hex[:8]}")

        return {
            "event": "on_step",
            "data": {
                "id": step_id,
                "name": event.get("name", "Processing"),
                "status": "completed",
                "started_at": None,  # Not available in end event
                "completed_at": datetime.utcnow().isoformat(),
                "metadata": event.get("data", {}),
            },
            "metadata": event.get("metadata", {}),
        }

    def _transform_chat_model_end(self, event: dict[str, Any]) -> dict[str, Any]:
        """Transform on_chat_model_end → on_message_complete."""
        # Extract the final AIMessage from the output
        output = event.get("data", {}).get("output", {})

        # Handle both raw message objects and serialized content
        if hasattr(output, "content"):
            content = output.content
        elif isinstance(output, dict):
            content = output.get("content", "")
        else:
            content = str(output) if output else ""

        return {
            "event": "on_message_complete",
            "data": {
                "id": event.get("run_id", f"msg_{uuid.uuid4().hex[:8]}"),
                "content": content,
                "completed_at": datetime.utcnow().isoformat(),
                "finish_reason": "stop",
            },
            "metadata": event.get("metadata", {}),
        }
