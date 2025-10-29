"""
Event serialization utilities for converting LangChain objects to JSON-safe dictionaries.

Handles serialization of LangChain message objects (HumanMessage, AIMessage, etc.)
for WebSocket streaming and API responses.
"""

from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.messages.ai import AIMessageChunk


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
    return _serialize_value(event)


def _serialize_value(value: Any) -> Any:
    """
    Recursively serialize a value to be JSON-safe.

    Handles:
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

    # Return JSON-safe types as-is
    return value


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
