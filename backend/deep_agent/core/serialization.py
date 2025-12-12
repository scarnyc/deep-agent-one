"""
Event serialization utilities for converting LangChain objects to JSON-safe dictionaries.

Handles serialization of LangChain message objects (HumanMessage, AIMessage, etc.)
for WebSocket streaming and API responses.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from deep_agent.core.logging import get_logger

# Type checking imports (not executed at runtime)
if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage
    from langchain_core.messages.ai import AIMessageChunk
    from langgraph.types import Send


def _lazy_import_langchain_types():
    """Lazy import of LangChain types to avoid blocking at module load time."""
    from langchain_core.messages import BaseMessage
    from langchain_core.messages.ai import AIMessageChunk
    from langgraph.types import Send
    return BaseMessage, AIMessageChunk, Send

logger = get_logger(__name__)


def serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively serialize an event dictionary to be JSON-safe.

    Converts LangChain BaseMessage objects to dictionaries and handles
    nested structures (lists, dicts) containing non-JSON-serializable objects.

    Args:
        event: Event dictionary from agent.astream_events()

    Returns:
        JSON-serializable dictionary

    Example:
        >>> from langchain_core.messages import HumanMessage
        >>> event = {
        ...     "data": {
        ...         "messages": [HumanMessage(content="Hello")],
        ...         "metadata": {"step": 1}
        ...     }
        ... }
        >>> serialized = serialize_event(event)
        >>> serialized["data"]["messages"][0]
        {'type': 'human', 'content': 'Hello', ...}
    """
    try:
        return _serialize_value(event)
    except Exception as e:
        logger.error(
            "Event serialization failed",
            error=str(e),
            error_type=type(e).__name__,
            event_type=event.get("event") if isinstance(event, dict) else None,
            event_keys=list(event.keys()) if isinstance(event, dict) else None,
        )
        # Return minimal safe event for debugging
        return {
            "event": event.get("event", "unknown") if isinstance(event, dict) else "unknown",
            "status": "error",
            "message": "Event serialization failed.",
        }


def _serialize_value(value: Any) -> Any:
    """
    Recursively serialize a value to be JSON-safe.

    Handles:
    - Send objects (LangGraph tool routing)
    - BaseMessage objects (HumanMessage, AIMessage, SystemMessage, etc.)
    - AIMessageChunk objects (streaming token chunks)
    - Dictionaries (recursive)
    - Lists (recursive)
    - All other JSON-safe types (str, int, float, bool, None)

    Args:
        value: Value to serialize

    Returns:
        JSON-serializable equivalent of the value
    """
    # Lazy import types to avoid blocking at module load time
    BaseMessage, AIMessageChunk, Send = _lazy_import_langchain_types()

    # Handle LangGraph Send objects (tool routing) - MUST BE FIRST
    # Send objects are used by LangGraph to route tool calls to tool nodes
    if isinstance(value, Send):
        return _serialize_send(value)

    # Handle LangChain message chunks (streaming tokens)
    if isinstance(value, AIMessageChunk):
        return _serialize_message_chunk(value)

    # Handle LangChain message objects
    if isinstance(value, BaseMessage):
        return _serialize_message(value)

    # Handle dictionaries recursively
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}

    # Handle lists recursively
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    # Handle tuples (convert to list)
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]

    # Final fallback: try to JSON-serialize, or convert to string
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        # Object is not JSON-serializable, log and convert to safe string
        logger.debug(
            "Converting non-JSON-serializable object to string",
            object_type=type(value).__name__,
            str_repr=str(value)[:100],
        )
        return f"<{type(value).__name__}: {str(value)[:50]}>"


def _serialize_message_chunk(chunk: AIMessageChunk) -> dict[str, Any]:
    """
    Serialize an AIMessageChunk object (streaming token) to a dictionary.

    Args:
        chunk: AIMessageChunk from on_chat_model_stream event

    Returns:
        Dictionary with chunk content and metadata

    Example:
        >>> from langchain_core.messages.ai import AIMessageChunk
        >>> chunk = AIMessageChunk(content="Hello", id="chunk-123")
        >>> _serialize_message_chunk(chunk)
        {
            'type': 'ai_chunk',
            'content': 'Hello',
            'id': 'chunk-123'
        }
    """
    serialized = {
        "type": "ai_chunk",
        "content": chunk.content if hasattr(chunk, "content") else str(chunk),
    }

    # Add optional fields if present
    if hasattr(chunk, "id") and chunk.id:
        serialized["id"] = chunk.id

    if hasattr(chunk, "additional_kwargs") and chunk.additional_kwargs:
        serialized["additional_kwargs"] = _serialize_value(chunk.additional_kwargs)

    if hasattr(chunk, "response_metadata") and chunk.response_metadata:
        serialized["response_metadata"] = _serialize_value(chunk.response_metadata)

    return serialized


def _serialize_message(message: BaseMessage) -> dict[str, Any]:
    """
    Serialize a LangChain BaseMessage object to a dictionary.

    Args:
        message: LangChain message (HumanMessage, AIMessage, etc.)

    Returns:
        Dictionary with message type, content, and metadata

    Example:
        >>> from langchain_core.messages import HumanMessage
        >>> msg = HumanMessage(content="Hello", id="123")
        >>> _serialize_message(msg)
        {
            'type': 'human',
            'content': 'Hello',
            'id': '123',
            'additional_kwargs': {},
            'response_metadata': {}
        }
    """
    # Get message type (human, ai, system, etc.)
    message_type = message.__class__.__name__.lower().replace("message", "")

    # Build serialized message
    serialized = {
        "type": message_type,
        "content": message.content,
    }

    # Add optional fields if present
    if hasattr(message, "id") and message.id:
        serialized["id"] = message.id

    if hasattr(message, "additional_kwargs") and message.additional_kwargs:
        serialized["additional_kwargs"] = _serialize_value(message.additional_kwargs)

    if hasattr(message, "response_metadata") and message.response_metadata:
        serialized["response_metadata"] = _serialize_value(message.response_metadata)

    if hasattr(message, "name") and message.name:
        serialized["name"] = message.name

    return serialized


def _serialize_send(send: Send) -> dict[str, Any]:
    """
    Serialize a LangGraph Send object to a dictionary.

    Send objects are used by LangGraph to route work to specific nodes in the graph.
    For example, when an agent decides to call a tool, it creates a Send object
    to route the tool invocation to the tools node.

    Args:
        send: LangGraph Send object containing node routing information

    Returns:
        Dictionary with Send object data

    Example:
        >>> from langgraph.types import Send
        >>> send = Send(node="tools", arg={"tool": "web_search", "query": "weather"})
        >>> _serialize_send(send)
        {
            'type': 'send',
            'node': 'tools',
            'arg': {'tool': 'web_search', 'query': 'weather'}
        }
    """
    serialized = {
        "type": "send",
    }

    # Add node name if present
    if hasattr(send, "node") and send.node is not None:
        serialized["node"] = send.node

    # Recursively serialize the argument (may contain complex objects)
    if hasattr(send, "arg") and send.arg is not None:
        serialized["arg"] = _serialize_value(send.arg)

    return serialized
