# Models

## Purpose

Pydantic data models for request/response validation, configuration, and data transfer objects across the Deep Agent One application. All models use Pydantic v2 for runtime validation, JSON schema generation, and type safety.

## Key Files

- **`__init__.py`** - Package initialization with model exports
- **`agents.py`** - Agent management models (run tracking, HITL workflows, errors)
- **`chat.py`** - Chat API models (messages, requests, responses, streaming events)
- **`gpt5.py`** - GPT-5 configuration models (reasoning effort, verbosity, ChatOpenAI config)

## Usage

### API Models

#### Chat Request/Response

```python
from deep_agent.models import ChatRequest, ChatResponse, Message, MessageRole, ResponseStatus

# Create a chat request
request = ChatRequest(
    message="What files are in my project?",
    thread_id="user-123",
    metadata={"source": "web", "user_id": "12345"}
)

# Create a chat response
msg = Message(role=MessageRole.ASSISTANT, content="Here are your files...")
response = ChatResponse(
    messages=[msg],
    thread_id="user-123",
    status=ResponseStatus.SUCCESS,
    trace_id="trace-abc-456",
    run_id="run-def-789"
)
```

#### Streaming Events

```python
from deep_agent.models import StreamEvent

# Create a streaming event
event = StreamEvent(
    event_type="on_chat_model_stream",
    data={"content": "Hello, how can I help you today?"},
    thread_id="user-123"
)

# Serialize to SSE format
sse_data = f"event: {event.event_type}\ndata: {event.model_dump_json()}\n\n"
```

### Agent Models

#### Agent Run Tracking

```python
from deep_agent.models import AgentRunInfo, AgentRunStatus

# Create run info
run_info = AgentRunInfo(
    run_id="run-abc-123",
    thread_id="user-456",
    status=AgentRunStatus.RUNNING,
    trace_id="trace-xyz-789"
)

# Update status on completion
run_info.status = AgentRunStatus.COMPLETED
run_info.completed_at = datetime.now(timezone.utc)
```

#### HITL Approval Workflow

```python
from deep_agent.models import HITLApprovalRequest, HITLApprovalResponse, HITLAction

# User accepts agent action
approval_request = HITLApprovalRequest(
    run_id="run-abc-123",
    thread_id="user-456",
    action=HITLAction.ACCEPT
)

# User provides feedback
approval_request = HITLApprovalRequest(
    run_id="run-abc-123",
    thread_id="user-456",
    action=HITLAction.RESPOND,
    response_text="Please also check the logs directory"
)

# User edits tool parameters
approval_request = HITLApprovalRequest(
    run_id="run-abc-123",
    thread_id="user-456",
    action=HITLAction.EDIT,
    tool_edits={"path": "/home/user/logs", "recursive": True}
)

# Create approval response
approval_response = HITLApprovalResponse(
    success=True,
    message="Action approved and executed",
    run_id="run-abc-123",
    thread_id="user-456",
    updated_status=AgentRunStatus.RUNNING
)
```

### Configuration Models

#### GPT-5 Configuration

```python
from deep_agent.models import GPT5Config, ReasoningEffort, Verbosity

# Create config for deep reasoning with concise output
config = GPT5Config(
    model_name="gpt-5",
    reasoning_effort=ReasoningEffort.HIGH,
    verbosity=Verbosity.LOW,
    max_tokens=4096,
    temperature=0.7
)

# Use with LLMFactory
from deep_agent.llm.factory import LLMFactory
factory = LLMFactory()
llm = factory.create_llm(
    model_type="gpt5",
    reasoning_effort=config.reasoning_effort,
    verbosity=config.verbosity
)
```

### Error Handling

```python
from deep_agent.models import ErrorResponse
from pydantic import ValidationError

# Create error response
error = ErrorResponse(
    error="Agent execution failed",
    detail="Connection timeout after 30 seconds",
    thread_id="user-123",
    trace_id="trace-abc-456",
    run_id="run-def-789"
)

# Handle validation errors
try:
    request = ChatRequest(message="", thread_id="user-123")  # Empty message
except ValidationError as e:
    print(e.errors())
    # [{'type': 'string_too_short', 'loc': ('message',), 'msg': 'String should have at least 1 character', ...}]
```

## Validation

### Field Validators

All models implement comprehensive validation:

#### String Validation
```python
# Automatically strips whitespace and validates non-empty
request = ChatRequest(message="  Hello  ", thread_id="  user-123  ")
# Becomes: message="Hello", thread_id="user-123"

# Rejects empty/whitespace-only strings
try:
    ChatRequest(message="   ", thread_id="user-123")
except ValidationError as e:
    print(e)  # ValueError: Content cannot be empty or whitespace-only
```

#### Metadata Validation (Security)
```python
from deep_agent.models import ChatRequest

# Validates metadata size (max 10KB)
large_metadata = {"data": "x" * 20000}
try:
    ChatRequest(message="Hello", thread_id="user-123", metadata=large_metadata)
except ValidationError as e:
    print(e)  # ValueError: Metadata payload too large (20000 bytes, max 10000 bytes)

# Validates nesting depth (max 5 levels)
deeply_nested = {"a": {"b": {"c": {"d": {"e": {"f": "too deep"}}}}}}
try:
    ChatRequest(message="Hello", thread_id="user-123", metadata=deeply_nested)
except ValidationError as e:
    print(e)  # ValueError: Metadata nesting too deep (max 5 levels)
```

#### Timestamp Validation
```python
from deep_agent.models import Message, MessageRole

# Auto-generates UTC timestamps
msg = Message(role=MessageRole.USER, content="Hello")
print(msg.timestamp)  # 2025-01-01 12:00:00+00:00 (current UTC time)
```

## Model Categories

### API Models
Request/response models for FastAPI endpoints:
- `ChatRequest` - User message with thread_id and metadata
- `ChatResponse` - Agent response with messages, status, trace_id
- `StreamEvent` - Server-Sent Event for streaming updates

### Agent Models
Agent execution and HITL workflow models:
- `AgentRunInfo` - Run tracking with status, timing, metadata
- `HITLApprovalRequest` - Human approval/rejection/editing actions
- `HITLApprovalResponse` - Approval action result
- `AgentRunStatus` - Enum (running, completed, error, interrupted)
- `HITLAction` - Enum (accept, respond, edit)

### Error Models
Error response models for consistent error handling:
- `ErrorResponse` - Generic error with trace_id, run_id, detail

### Config Models
Configuration models for LLM and agent settings:
- `GPT5Config` - ChatOpenAI configuration with reasoning/verbosity
- `ReasoningEffort` - Enum (minimal, low, medium, high)
- `Verbosity` - Enum (low, medium, high)

### Enum Models
Enumeration types for standardized values:
- `MessageRole` - user, assistant, system
- `ResponseStatus` - success, error, pending
- `AgentRunStatus` - running, completed, error, interrupted
- `HITLAction` - accept, respond, edit

## Design Patterns

### Pydantic v2 Validation

All models use Pydantic v2 features:

```python
from pydantic import BaseModel, Field, field_validator

class ExampleModel(BaseModel):
    """Example model with validation."""

    name: str = Field(
        min_length=1,
        description="User-friendly name"
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_and_validate_name(cls, v: Any) -> str:
        """Strip whitespace and validate name is not empty."""
        if not isinstance(v, str):
            raise ValueError("Name must be a string")

        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or whitespace-only")

        return stripped
```

### Field Validators with @field_validator

Custom validation logic for complex fields:

```python
@field_validator("metadata", mode="before")
@classmethod
def validate_metadata_size_and_depth(cls, v: Any) -> dict[str, Any] | None:
    """
    Validate metadata dict is not too large or deeply nested.

    Security constraints:
    - Maximum serialized size: 10KB (prevents DoS via large payloads)
    - Maximum nesting depth: 5 levels (prevents RecursionError)
    """
    if v is None:
        return None

    # Validate size and depth...
    return v
```

### Config Class for Model Behavior

Configure JSON schema generation and examples:

```python
model_config = {
    "json_schema_extra": {
        "example": {
            "message": "What files are in my project?",
            "thread_id": "user-456",
            "metadata": {"source": "web", "user_id": "12345"}
        }
    }
}
```

### Type Hints for All Fields

Full type safety with modern Python typing:

```python
from typing import Any, Optional

messages: list[Message] = Field(
    min_length=1,
    description="List of messages in the conversation"
)
metadata: Optional[dict[str, Any]] = Field(
    default=None,
    description="Optional metadata about the request"
)
```

## Security Features

### DoS Prevention

- **Metadata size limit:** 10KB max to prevent memory exhaustion
- **Nesting depth limit:** 5 levels max to prevent RecursionError
- **String validation:** Strip whitespace, reject empty strings

### Input Sanitization

- **Whitespace stripping:** All strings trimmed before validation
- **Non-empty validation:** Reject empty or whitespace-only strings
- **Type checking:** Validate types before processing

### JSON Serialization

- **Metadata enforcement:** Must be JSON-serializable
- **Schema validation:** Pydantic ensures valid JSON structure
- **Example schemas:** Documented in `model_config`

## Dependencies

### External
- **pydantic**: v2.x - Data validation and settings management

### Internal
- None - Models have no internal dependencies (pure data models)

## Related Documentation

- **API**: [../api/README.md](../api/README.md) - FastAPI endpoints using these models
- **Services**: [../services/README.md](../services/README.md) - Business logic consuming these models
- **LLM**: [../llm/README.md](../llm/README.md) - GPT-5 configuration using GPT5Config

## Testing

### Unit Tests
```bash
# Run model validation tests
pytest tests/unit/test_models/ -v

# Test specific model
pytest tests/unit/test_models/test_chat.py -v

# Test with coverage
pytest tests/unit/test_models/ --cov=deep_agent.models --cov-report=html
```

### Test Files
- `tests/unit/test_models/test_agents.py` - Agent model validation
- `tests/unit/test_models/test_chat.py` - Chat model validation
- `tests/unit/test_models/test_gpt5.py` - GPT-5 config validation

### Example Test

```python
import pytest
from pydantic import ValidationError
from deep_agent.models import ChatRequest

def test_chat_request_validates_empty_message():
    """Test that ChatRequest rejects empty messages."""
    with pytest.raises(ValidationError) as exc_info:
        ChatRequest(message="", thread_id="user-123")

    assert "String should have at least 1 character" in str(exc_info.value)

def test_chat_request_strips_whitespace():
    """Test that ChatRequest strips whitespace from strings."""
    request = ChatRequest(message="  Hello  ", thread_id="  user-123  ")
    assert request.message == "Hello"
    assert request.thread_id == "user-123"
```

## Migration Guide

### From v1 to v2

If migrating from Pydantic v1:

```python
# Pydantic v1 (OLD)
class OldModel(BaseModel):
    class Config:
        schema_extra = {"example": {...}}

# Pydantic v2 (NEW)
class NewModel(BaseModel):
    model_config = {
        "json_schema_extra": {"example": {...}}
    }
```

### Validator Changes

```python
# Pydantic v1 (OLD)
@validator("field")
def validate_field(cls, v):
    return v

# Pydantic v2 (NEW)
@field_validator("field", mode="before")
@classmethod
def validate_field(cls, v: Any) -> str:
    return v
```

## Best Practices

1. **Always use Field() with description** - Generates better API docs
2. **Validate early** - Use `mode="before"` for pre-processing
3. **Type hints everywhere** - Enable static type checking with mypy
4. **Meaningful examples** - Add `json_schema_extra` with realistic examples
5. **Security first** - Validate size, depth, and content of user inputs
6. **Strip whitespace** - Always trim strings before validation
7. **UTC timestamps** - Use `datetime.now(timezone.utc)` for consistency

## Common Patterns

### Auto-Generated Timestamps

```python
timestamp: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    description="When the event was created (UTC)"
)
```

### Optional Fields with Validation

```python
thread_id: Optional[str] = Field(
    default=None,
    description="Optional thread identifier"
)

@field_validator("thread_id", mode="before")
@classmethod
def validate_thread_id(cls, v: Any) -> str | None:
    """Validate thread_id if provided."""
    if v is None:
        return None

    if not isinstance(v, str):
        raise ValueError("Thread ID must be a string")

    stripped = v.strip()
    if not stripped:
        raise ValueError("Thread ID cannot be empty")

    return stripped
```

### Enum Defaults

```python
status: ResponseStatus = Field(
    default=ResponseStatus.PENDING,
    description="Status of the response"
)
```

## Troubleshooting

### ValidationError: String should have at least 1 character

**Cause:** Empty or whitespace-only string provided

**Solution:** Ensure strings are non-empty after stripping whitespace

```python
# Bad
ChatRequest(message="", thread_id="user-123")

# Good
ChatRequest(message="Hello", thread_id="user-123")
```

### ValidationError: Metadata payload too large

**Cause:** Metadata exceeds 10KB size limit

**Solution:** Reduce metadata size or move large data elsewhere

```python
# Bad
ChatRequest(message="Hi", thread_id="user-123", metadata={"large": "x" * 20000})

# Good
ChatRequest(message="Hi", thread_id="user-123", metadata={"key": "value"})
```

### ValidationError: Metadata nesting too deep

**Cause:** Metadata nesting exceeds 5 levels

**Solution:** Flatten metadata structure

```python
# Bad (6 levels)
metadata = {"a": {"b": {"c": {"d": {"e": {"f": "value"}}}}}}

# Good (3 levels)
metadata = {"a": {"b": {"c_d_e_f": "value"}}}
```
