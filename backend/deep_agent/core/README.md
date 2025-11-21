# Core

## Purpose

Core utilities and shared functionality used across the Deep Agent framework. This module provides foundational components including logging, error handling, security utilities, and serialization patterns that are used by all other modules.

## Key Files

- **`__init__.py`** - Core module exports and package documentation
- **`errors.py`** - Custom exception hierarchy for typed error handling
- **`logging.py`** - Structured logging setup with JSON output and LangSmith integration
- **`security.py`** - Security utilities for sanitizing secrets from logs and errors
- **`serialization.py`** - Event serialization for converting LangChain objects to JSON-safe dictionaries

## Usage

### Structured Logging

The logging module provides JSON-formatted structured logging with context fields for debugging and tracing.

```python
from deep_agent.core.logging import get_logger, setup_logging, LogLevel

# Configure logging once at application startup
setup_logging(log_level=LogLevel.INFO, log_format="json")

# Get logger for your module
logger = get_logger(__name__)

# Log with structured context
logger.info(
    "Agent processing user query",
    thread_id="thread-123",
    user_id="user-456",
    query_length=42
)

# Log errors with exception info
try:
    result = process_query(query)
except Exception as e:
    logger.error(
        "Query processing failed",
        thread_id="thread-123",
        error=str(e),
        exc_info=True
    )
```

**LangSmith Integration:**
```python
from deep_agent.core.logging import generate_langsmith_url

# Generate trace URL for debugging
trace_url = generate_langsmith_url(trace_id="abc-123-def")
logger.info("LangSmith trace available", trace_url=trace_url)
# Output: https://smith.langchain.com/public/abc-123-def/r
```

### Error Handling

The error module provides a typed exception hierarchy for different error categories.

```python
from deep_agent.core.errors import (
    DeepAgentError,
    ConfigurationError,
    LLMError,
    ToolError,
    MCPError,
    AuthenticationError,
    DatabaseError,
)

# Raise specific error types with context
raise ConfigurationError(
    "Missing API key",
    env_var="OPENAI_API_KEY",
    config_file=".env"
)

# Catch and handle specific errors
try:
    result = call_openai_api()
except LLMError as e:
    logger.error(
        "LLM API call failed",
        error=e.message,
        context=e.context
    )
    # Handle rate limits, retries, etc.

# Base exception catches all Deep Agent errors
try:
    execute_agent_task()
except DeepAgentError as e:
    logger.error("Agent task failed", error=e.message)
```

**Exception Hierarchy:**
```
DeepAgentError (base)
├── ConfigurationError - Missing or invalid configuration
├── LLMError - OpenAI API errors, rate limits, invalid models
├── ToolError - Tool execution failures (file ops, web search, etc.)
├── MCPError - MCP server connection or execution errors
├── AuthenticationError - Authentication/authorization failures
└── DatabaseError - Database operation errors
```

### Security Utilities

The security module prevents accidental exposure of API keys, tokens, and passwords in logs.

```python
from deep_agent.core.security import sanitize_error_message, mask_api_key

# Sanitize error messages before logging
error_msg = "Authentication failed with key: sk-proj-1234567890"
safe_msg = sanitize_error_message(error_msg)
logger.error(safe_msg)
# Output: "[REDACTED: Potential secret in error message]"

# Mask API keys for safe logging
api_key = "sk-proj-1234567890abcdefghij"
masked = mask_api_key(api_key)
logger.info("Using API key", masked_key=masked)
# Output: "sk-proj-1...ghij"

# Custom masking length
masked = mask_api_key(api_key, prefix_len=6, suffix_len=6)
# Output: "sk-pro...efghij"
```

**Protected Patterns:**
- OpenAI keys: `sk-`
- LangSmith tokens: `lsv2_`, `ls__`
- Generic patterns: `key=`, `token=`, `password=`, `api_key=`, `secret=`

### Event Serialization

The serialization module converts LangChain message objects to JSON-safe dictionaries for WebSocket streaming and API responses.

```python
from deep_agent.core.serialization import serialize_event
from langchain_core.messages import HumanMessage, AIMessage

# Serialize agent events for WebSocket
event = {
    "event": "on_chat_model_stream",
    "data": {
        "chunk": AIMessage(content="Hello!", id="msg-123"),
        "metadata": {"step": 1}
    }
}

serialized = serialize_event(event)
# Result:
# {
#     "event": "on_chat_model_stream",
#     "data": {
#         "chunk": {
#             "type": "ai",
#             "content": "Hello!",
#             "id": "msg-123"
#         },
#         "metadata": {"step": 1}
#     }
# }

# Handles nested structures
event = {
    "data": {
        "messages": [
            HumanMessage(content="What is AI?"),
            AIMessage(content="AI is...")
        ]
    }
}

serialized = serialize_event(event)
# Both messages converted to dictionaries
```

**Supported Types:**
- `BaseMessage` (HumanMessage, AIMessage, SystemMessage, ToolMessage)
- `AIMessageChunk` (streaming tokens)
- `Send` (LangGraph tool routing)
- Nested dictionaries and lists
- All JSON-safe primitives (str, int, float, bool, None)

## Design Patterns

### Structured Logging with Context

All modules use structured logging with context fields for rich debugging:

```python
logger.info(
    "User action",
    user_id=user_id,
    action="query",
    thread_id=thread_id,
    session_id=session_id
)
```

**Benefits:**
- JSON output for log aggregation (ELK, Datadog, etc.)
- Easy filtering and searching by context fields
- LangSmith trace URL generation for debugging
- Automatic timestamp and log level injection

### Custom Exception Hierarchy

All errors inherit from `DeepAgentError` for consistent error handling:

```python
# Service layer can catch base exception
try:
    agent_service.process_query(query)
except DeepAgentError as e:
    # All Deep Agent errors have .message and .context
    log_error(e.message, e.context)
    return error_response(e)

# API layer can catch specific errors
try:
    agent_service.process_query(query)
except LLMError as e:
    # Handle rate limits specifically
    return rate_limit_response(e)
except ToolError as e:
    # Handle tool failures differently
    return tool_error_response(e)
```

**Benefits:**
- Type-safe error handling
- Context preservation across layers
- Easy error categorization
- Consistent error logging

### Security-First Logging

All error messages and logs are sanitized to prevent secret leakage:

```python
# In service layer
try:
    openai_client.create(api_key=api_key)
except Exception as e:
    # Sanitize before logging
    safe_msg = sanitize_error_message(str(e))
    logger.error("OpenAI API call failed", error=safe_msg)
```

**Benefits:**
- No API keys in logs
- No tokens in error messages
- Safe log aggregation and sharing
- Compliance with security best practices

### Event-Driven Serialization

All LangChain objects are serialized for WebSocket streaming:

```python
# In WebSocket handler
async for event in agent.astream_events():
    # Serialize entire event (including nested messages)
    serialized = serialize_event(event)

    # Safe to send over WebSocket
    await websocket.send_json(serialized)
```

**Benefits:**
- No JSON serialization errors
- Consistent event format
- Handles all LangChain message types
- Graceful fallback for unknown types

## Dependencies

### External Dependencies

- **structlog** - Structured logging library with JSON output
- **pydantic** - Type validation (used by exception context)
- **langchain-core** - LangChain message types (BaseMessage, AIMessageChunk)
- **langgraph** - LangGraph types (Send objects)

### Internal Dependencies

None - this is the base module. All other modules depend on `core`.

## Related Documentation

- [Services](../services/README.md) - Uses logging, errors, and serialization
- [API](../api/README.md) - Uses errors for HTTP response mapping
- [Models](../models/README.md) - Uses errors for LLM client error handling
- [Tools](../tools/README.md) - Uses ToolError for tool execution failures

## Testing

### Unit Tests

Located in: `tests/unit/test_core/`

**Coverage:**
- `test_logging.py` - Logging configuration, context injection, LangSmith URLs
- `test_errors.py` - Exception hierarchy, context preservation
- `test_security.py` - Secret sanitization, API key masking
- `test_serialization.py` - Message serialization, event handling

**Run core tests:**
```bash
# All core tests
pytest tests/unit/test_core/ -v

# Specific test file
pytest tests/unit/test_core/test_logging.py -v

# With coverage
pytest tests/unit/test_core/ --cov=deep_agent.core --cov-report=html
```

### Integration Tests

Located in: `tests/integration/`

**Coverage:**
- End-to-end logging with LangSmith trace URLs
- Error propagation across service boundaries
- Event serialization in WebSocket handlers

**Run integration tests:**
```bash
pytest tests/integration/ -v -k "logging or serialization"
```

## Development Guidelines

### Adding New Exceptions

1. Inherit from `DeepAgentError` or a more specific subclass
2. Add docstring describing when to use the exception
3. Pass context via `**kwargs` in constructor
4. Add test cases in `tests/unit/test_core/test_errors.py`

```python
class NewError(DeepAgentError):
    """Raised when a specific condition occurs."""
    pass

# Usage
raise NewError(
    "Descriptive error message",
    context_field="value",
    another_field=123
)
```

### Adding Security Patterns

1. Add pattern to `SECRET_PATTERNS` list in `security.py`
2. Add test cases in `tests/unit/test_core/test_security.py`
3. Document pattern in this README

```python
SECRET_PATTERNS = [
    "sk-",  # OpenAI API keys
    "new_pattern_",  # Description
]
```

### Adding Serialization Support

1. Add handler in `_serialize_value()` function
2. Create dedicated `_serialize_<type>()` function
3. Add test cases in `tests/unit/test_core/test_serialization.py`

```python
def _serialize_value(value: Any) -> Any:
    # Add new type check
    if isinstance(value, NewType):
        return _serialize_new_type(value)

    # ... existing handlers

def _serialize_new_type(obj: NewType) -> dict[str, Any]:
    """Serialize NewType to dictionary."""
    return {
        "type": "new_type",
        "field": obj.field,
    }
```

## Performance Considerations

### Logging

- Use JSON format in production for fast parsing
- Use standard format in development for readability
- Log at appropriate levels (DEBUG for verbose, INFO for key events)
- Avoid logging inside tight loops (batch log instead)

### Serialization

- Serialization is recursive - deep nesting can be slow
- LangChain messages are immutable - cache serialized versions if possible
- Error fallback logs to DEBUG - graceful degradation for unknown types

### Security

- Sanitization patterns use simple string matching (fast)
- Masking is string slicing (constant time)
- No regex or complex parsing for performance

## Migration Notes

### From Standard Logging to Structured Logging

**Before:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing query {query_id} for user {user_id}")
```

**After:**
```python
from deep_agent.core.logging import get_logger
logger = get_logger(__name__)
logger.info("Processing query", query_id=query_id, user_id=user_id)
```

**Benefits:**
- Fields are queryable in log aggregation tools
- No string interpolation (safer, faster)
- Consistent JSON output format

### From Generic Exceptions to Typed Exceptions

**Before:**
```python
raise Exception("OpenAI API call failed")
```

**After:**
```python
from deep_agent.core.errors import LLMError
raise LLMError(
    "OpenAI API call failed",
    model="gpt-5-turbo",
    status_code=429
)
```

**Benefits:**
- Catch specific error types
- Preserve error context
- Better error handling logic
