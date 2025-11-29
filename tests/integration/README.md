# Integration Tests

**Location:** `/tests/integration/`

**Purpose:** Integration tests verify interactions between multiple components of the Deep Agent One system. Unlike unit tests that test isolated functions, integration tests ensure components work together correctly across architectural boundaries.

## Overview

Integration tests focus on:
- **Component interactions** (API → Service → Agent)
- **Realistic workflows** (user sends message → agent processes → response streams back)
- **Error propagation** (how errors flow through layers)
- **Protocol compliance** (SSE, WebSocket, AG-UI Protocol)
- **Data flow** (message transformation across layers)

Integration tests **mock external dependencies** (OpenAI API, Perplexity MCP) but test **real internal logic** (validation, routing, error handling).

---

## Directory Structure

```
tests/integration/
├── __init__.py                          # Package docstring
├── README.md                            # This file
│
├── test_agent_workflows/                # Agent service orchestration
│   ├── __init__.py
│   └── test_agent_service.py           # AgentService lifecycle & invocation
│
├── test_api_endpoints/                  # FastAPI endpoint tests
│   ├── __init__.py
│   ├── test_main.py                    # App startup, middleware, health
│   ├── test_chat.py                    # POST /api/v1/chat
│   ├── test_chat_stream.py             # POST /api/v1/chat/stream (SSE)
│   ├── test_websocket.py               # WebSocket /api/v1/ws
│   └── test_agents.py                  # Agent management (HITL)
│
├── test_mcp_integration/                # MCP client tests
│   ├── __init__.py
│   └── test_perplexity.py              # Perplexity MCP client
│
├── test_database/                       # Database integration (planned)
│   └── __init__.py
│
├── test_tool_event_streaming.py         # Event filter & streaming
└── test_websocket_cancellation.py       # WebSocket cancellation handling
```

---

## Test Categories

### 1. Agent Workflows (`test_agent_workflows/`)

**What:** Tests the `AgentService` orchestration layer that manages agent lifecycle.

**Components Tested:**
- `AgentService` (service layer)
- `create_agent()` factory
- LangGraph `CompiledStateGraph`
- Agent invocation and streaming

**Test Scenarios:**
```python
# Agent creation (lazy loading)
service = AgentService(settings=mock_settings)
assert service.agent is None  # Not created until first use

# Agent invocation
result = await service.invoke("Hello", "thread-123")
assert result["messages"][-1]["role"] == "assistant"

# Streaming
async for event in service.stream("Hello", "thread-123"):
    assert event["event"] in allowed_events

# Input validation
with pytest.raises(ValueError, match="Message cannot be empty"):
    await service.invoke("", "thread-123")

# Error propagation
mock_agent.ainvoke.side_effect = RuntimeError("Execution failed")
with pytest.raises(RuntimeError):
    await service.invoke("Hello", "thread-123")
```

**Mocking:**
- ✓ Mock `LangGraph.CompiledStateGraph`
- ✓ Mock `create_agent()` factory
- ✓ Mock `Settings`
- ✗ Real input validation logic

---

### 2. API Endpoints (`test_api_endpoints/`)

**What:** Tests FastAPI endpoints, middleware, and protocol compliance.

**Endpoints Tested:**
- `POST /api/v1/chat` - Synchronous chat
- `POST /api/v1/chat/stream` - Server-Sent Events (SSE)
- `WebSocket /api/v1/ws` - Bidirectional communication
- `GET /api/v1/agents/{thread_id}` - Agent status
- `POST /api/v1/agents/{thread_id}/approve` - HITL approval

**Test Scenarios:**
```python
# Synchronous chat
response = client.post("/api/v1/chat", json={
    "message": "Hello",
    "thread_id": "test-123"
})
assert response.status_code == 200
assert response.json()["status"] == "success"

# SSE streaming
with client.stream("POST", "/api/v1/chat/stream", json={...}) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            assert "event" in event

# WebSocket
with client.websocket_connect("/api/v1/ws") as websocket:
    websocket.send_json({"type": "chat", "message": "Hello", ...})
    event = websocket.receive_json()
    assert "event" in event

# HITL approval
response = client.post("/api/v1/agents/thread-123/approve", json={
    "run_id": "run-456",
    "action": "accept"
})
assert response.json()["success"] is True
```

**Mocking:**
- ✓ Mock `AgentService` (agent execution)
- ✗ Real FastAPI `TestClient`
- ✗ Real request validation (Pydantic)
- ✗ Real middleware (CORS, rate limiting)

---

### 3. MCP Integration (`test_mcp_integration/`)

**What:** Tests Model Context Protocol client implementations.

**Clients Tested:**
- `PerplexityClient` - Web search

**Test Scenarios:**
```python
# Successful search
client = PerplexityClient(settings=mock_settings)
result = await client.search("python machine learning")
assert result["results"]
assert result["sources"] == 2

# Input validation
with pytest.raises(ValueError, match="Search query cannot be empty"):
    await client.search("")

# Error handling
mock_call_mcp.side_effect = TimeoutError("MCP request timed out")
with pytest.raises(TimeoutError):
    await client.search("test query")

# Response formatting
formatted = client.format_results_for_agent(result)
assert "Test Result 1" in formatted
assert "https://example.com/result1" in formatted
```

**Mocking:**
- ✓ Mock `_call_mcp()` (MCP protocol layer)
- ✓ Mock `Settings`
- ✗ Real validation logic
- ✗ Real response formatting

---

### 4. Tool Event Streaming (`test_tool_event_streaming.py`)

**What:** Regression tests for event filtering and streaming configuration.

**Test Scenarios:**
```python
# Verify tool events in allowed list
assert "on_tool_call_start" in allowed_events
assert "on_tool_call_end" in allowed_events

# Test event filter logic
passed, filtered = filter_events(test_events)
tool_events = [e for e in passed if "tool" in e["event"]]
assert len(tool_events) == 2

# Verify timeout configuration
assert settings.STREAM_TIMEOUT_SECONDS >= 180
```

**Context:** Regression tests for Issue #113 (agent timeout with parallel tools).

---

### 5. WebSocket Cancellation (`test_websocket_cancellation.py`)

**What:** Tests graceful cancellation handling when client disconnects.

**Test Scenarios:**
```python
# Verify CancelledError handler exists
source = source_file.read_text()
assert "except asyncio.CancelledError" in source

# Verify normal execution unaffected
result = await web_search.ainvoke({"query": "test", ...})
assert isinstance(result, str)
```

**Note:** Phase 0 uses mock Perplexity implementation, so timing-based cancellation tests are deferred to Phase 1.

---

### 6. Database Integration (`test_database/`)

**What:** Tests database operations (checkpointer, state persistence).

**Status:** Planned for Phase 0 completion. Currently tested indirectly via agent workflow tests.

**Planned Tests:**
- Checkpoint creation and retrieval
- Thread state persistence
- Checkpoint cleanup/expiration
- Concurrent access patterns

---

## Running Integration Tests

### All Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=backend.deep_agent --cov-report=html

# Parallel execution (faster)
pytest tests/integration/ -n auto
```

### Specific Test Suites

```bash
# Agent workflows only
pytest tests/integration/test_agent_workflows/ -v

# API endpoints only
pytest tests/integration/test_api_endpoints/ -v

# MCP integration only
pytest tests/integration/test_mcp_integration/ -v

# Event streaming regression tests
pytest tests/integration/test_tool_event_streaming.py -v

# WebSocket cancellation tests
pytest tests/integration/test_websocket_cancellation.py -v
```

### By Test Marker

```bash
# Integration tests only (exclude live API)
pytest -m integration -v

# Async tests only
pytest -m asyncio tests/integration/ -v
```

---

## Writing Integration Tests

### Best Practices

1. **Test Component Interactions, Not Isolated Units**
   ```python
   # GOOD: Tests API → Service interaction
   response = client.post("/api/v1/chat", json={"message": "Hello", ...})
   mock_agent_service.invoke.assert_called_once()

   # BAD: Tests single function in isolation (use unit tests instead)
   result = validate_message("Hello")
   assert result is True
   ```

2. **Mock External Dependencies Only**
   ```python
   # GOOD: Mock AgentService (external to API layer)
   with patch("backend.deep_agent.api.v1.chat.AgentService") as mock:
       response = client.post("/api/v1/chat", ...)

   # BAD: Mock internal validation (should test real validation)
   with patch("backend.deep_agent.models.chat.ChatRequest.validate"):
       ...  # Don't do this
   ```

3. **Use Realistic Test Data**
   ```python
   # GOOD: Realistic chat request
   request_data = {
       "message": "What are the latest trends in Gen AI?",
       "thread_id": "user-123-session-456",
       "metadata": {"user_id": "user-123", "source": "web"}
   }

   # BAD: Minimal/unrealistic data
   request_data = {"message": "test", "thread_id": "1"}
   ```

4. **Test Both Happy Path and Error Cases**
   ```python
   # Happy path
   def test_chat_success(client, mock_agent_service):
       response = client.post("/api/v1/chat", json={...})
       assert response.status_code == 200

   # Error case
   def test_chat_agent_error(client, mock_agent_service):
       mock_agent_service.invoke.side_effect = RuntimeError("Agent failed")
       response = client.post("/api/v1/chat", json={...})
       assert response.status_code == 500
   ```

5. **Verify Error Propagation Across Layers**
   ```python
   # Test error flows through all layers
   mock_agent.ainvoke.side_effect = RuntimeError("DB connection failed")

   response = client.post("/api/v1/chat", json={...})

   # Verify error reached API layer
   assert response.status_code == 500
   assert "error" in response.json()
   ```

---

### Test Structure (AAA Pattern)

```python
@pytest.mark.asyncio
async def test_agent_service_invocation(
    mock_settings: Settings,
    mock_agent: CompiledStateGraph,
) -> None:
    """Test invoking agent with a simple user message.

    Scenario:
        User sends "Hello, agent!" via AgentService

    Components Involved:
        - AgentService (orchestration)
        - create_agent() (agent factory)
        - CompiledStateGraph.ainvoke() (LangGraph)

    Expected Behavior:
        - Agent created lazily on first invoke
        - Message passed to agent correctly
        - Response contains assistant message
        - Thread ID propagated to agent config
    """
    # Arrange: Set up test data and mocks
    with patch("backend.deep_agent.services.agent_service.create_agent") as mock_create:
        mock_create.return_value = mock_agent
        service = AgentService(settings=mock_settings)

    # Act: Execute the operation being tested
    result = await service.invoke(
        message="Hello, agent!",
        thread_id="test-thread-123"
    )

    # Assert: Verify expectations
    assert result is not None
    assert "messages" in result
    assert result["messages"][-1]["role"] == "assistant"
    assert "Test response" in result["messages"][-1]["content"]

    # Verify interactions
    mock_create.assert_called_once_with(settings=mock_settings, subagents=None)
    mock_agent.ainvoke.assert_called_once()
    call_args = mock_agent.ainvoke.call_args
    assert call_args[0][0]["messages"][0]["content"] == "Hello, agent!"
    assert call_args[0][1]["configurable"]["thread_id"] == "test-thread-123"
```

---

### Fixture Patterns

#### 1. Settings Fixture

```python
@pytest.fixture
def mock_settings(tmp_path: Path) -> Settings:
    """Fixture providing mocked Settings for tests."""
    settings = Mock(spec=Settings)
    settings.ENV = "local"
    settings.OPENAI_API_KEY = "sk-test-key-12345"
    settings.CHECKPOINT_DB_PATH = str(tmp_path / "test_checkpoints.db")
    settings.ENABLE_HITL = True
    return settings
```

#### 2. Mock Service Fixture

```python
@pytest.fixture
def mock_agent_service() -> AsyncMock:
    """Mock AgentService for testing without actual agent execution."""
    mock_service = AsyncMock()

    # Configure mock behavior
    mock_service.invoke.return_value = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
    }

    return mock_service
```

#### 3. FastAPI Client Fixture

```python
@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client.

    Imports app here to avoid circular dependencies and ensure
    fresh app instance for each test.
    """
    from backend.deep_agent.main import app
    return TestClient(app)
```

#### 4. Mock Async Generator Fixture

```python
@pytest.fixture
def mock_agent_service_with_streaming() -> AsyncMock:
    """Mock AgentService with streaming support."""
    mock_service = AsyncMock()

    async def mock_stream(*args, **kwargs):
        """Mock async generator for streaming events."""
        events = [
            {"event": "on_chat_model_start", "data": {...}},
            {"event": "on_chat_model_stream", "data": {"chunk": {"content": "Hi "}}},
            {"event": "on_chat_model_end", "data": {...}},
        ]
        for event in events:
            yield event

    # Important: Assign function, don't call it
    mock_service.stream.side_effect = mock_stream

    return mock_service
```

---

## What to Test vs. What to Mock

### Mock External Dependencies

✓ **Mock These:**
- OpenAI API calls (`ChatOpenAI`, `AzureChatOpenAI`)
- Perplexity MCP server connections
- External HTTP requests
- Third-party services (Gmail, Calendar, GitHub)
- Time-dependent operations (`time.sleep`, `datetime.now`)

### Test Real Internal Logic

✗ **Don't Mock These:**
- Request validation (Pydantic models)
- Response formatting
- Error handling logic
- Middleware (CORS, rate limiting)
- Database operations (use test DB)
- Internal function calls within same layer

---

## Test Scenarios by Component

### API → Service → Agent Flow

```python
# Test complete flow with mocked agent execution
@pytest.mark.asyncio
async def test_complete_chat_flow(client, mock_agent_service):
    """Test API → AgentService → Agent flow."""
    # User sends request via API
    response = client.post("/api/v1/chat", json={
        "message": "Hello",
        "thread_id": "test-123"
    })

    # Verify API layer processed request
    assert response.status_code == 200

    # Verify service layer was invoked
    mock_agent_service.invoke.assert_called_once()
    call_kwargs = mock_agent_service.invoke.call_args[1]
    assert call_kwargs["message"] == "Hello"
    assert call_kwargs["thread_id"] == "test-123"

    # Verify response format
    data = response.json()
    assert data["status"] == "success"
    assert data["thread_id"] == "test-123"
```

### Streaming Workflows

```python
# Test SSE streaming
def test_sse_streaming(client, mock_agent_service):
    """Test Server-Sent Events streaming."""
    with client.stream("POST", "/api/v1/chat/stream", json={...}) as response:
        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                events.append(event)

        # Verify event sequence
        assert len(events) >= 3  # start + content + end
        assert events[0]["event"] == "on_chat_model_start"
        assert events[-1]["event"] == "on_chat_model_end"
```

### HITL Workflows

```python
# Test Human-in-the-Loop approval
def test_hitl_approval(client, mock_agent_service):
    """Test HITL approval workflow."""
    # 1. Get agent status (waiting for approval)
    status_response = client.get("/api/v1/agents/thread-123")
    assert status_response.json()["status"] == "waiting_for_approval"

    # 2. User approves action
    approve_response = client.post("/api/v1/agents/thread-123/approve", json={
        "run_id": "run-456",
        "action": "accept"
    })
    assert approve_response.json()["success"] is True

    # 3. Verify update_state was called
    mock_agent_service.update_state.assert_called_once()
```

### Error Propagation

```python
# Test error flows through all layers
def test_error_propagation(client, mock_agent_service):
    """Test error propagates from service to API layer."""
    # Mock service to raise error
    mock_agent_service.invoke.side_effect = RuntimeError("Agent execution failed")

    # Make request
    response = client.post("/api/v1/chat", json={...})

    # Verify error handled at API layer
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"].lower()
```

---

## Coverage Expectations

### Integration Test Coverage Goals

- **Overall:** 80%+ combined coverage (unit + integration)
- **Integration-specific:** Focus on multi-component interactions
- **Critical paths:** 100% coverage for user-facing workflows
- **Error scenarios:** Cover major failure modes

### What Integration Tests Should Cover

✓ **Cover These:**
- API endpoint request/response handling
- Service layer orchestration
- Error propagation across boundaries
- Protocol compliance (SSE, WebSocket, AG-UI)
- Input validation at API boundaries
- Rate limiting enforcement
- HITL approval workflows
- Event streaming and filtering

✗ **Don't Duplicate Unit Test Coverage:**
- Individual function logic (use unit tests)
- Detailed edge cases within single component
- Complex conditional branches in isolated functions

---

## Dependencies

### Test Dependencies

```toml
[tool.poetry.group.test.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.12.0"
httpx = "^0.27.0"                    # FastAPI TestClient
pytest-xdist = "^3.5.0"              # Parallel test execution
```

### Import Patterns

```python
# Standard imports
import pytest
from unittest.mock import AsyncMock, Mock, patch

# FastAPI testing
from fastapi.testclient import TestClient

# Internal imports (use absolute paths)
from backend.deep_agent.services.agent_service import AgentService
from backend.deep_agent.config.settings import Settings
from backend.deep_agent.models.chat import ChatRequest, ChatResponse
```

---

## Related Documentation

- **Unit Tests:** `/tests/unit/README.md` - Isolated component tests
- **E2E Tests:** `/tests/e2e/README.md` - Complete user workflows (planned)
- **Live API Tests:** `/tests/live_api/README.md` - Real API integration (Phase 0.5)
- **Test Strategy:** `/docs/development/testing.md` - Overall testing approach
- **Architecture:** `/README.md` - System architecture and components

---

## Debugging Integration Tests

### Enable Verbose Logging

```bash
# Show print statements and logs
pytest tests/integration/ -v -s

# Show captured logs
pytest tests/integration/ --log-cli-level=DEBUG
```

### Run Single Test

```bash
# Run specific test
pytest tests/integration/test_api_endpoints/test_chat.py::TestChatEndpoint::test_chat_endpoint_success -v

# Run test class
pytest tests/integration/test_api_endpoints/test_chat.py::TestChatEndpoint -v
```

### Debug with pdb

```python
# Add breakpoint in test
def test_something(client):
    response = client.post("/api/v1/chat", json={...})
    import pdb; pdb.set_trace()  # Debugger drops in here
    assert response.status_code == 200
```

### View Mock Call Details

```python
# Inspect mock calls
mock_agent_service.invoke.assert_called_once()
print(mock_agent_service.invoke.call_args)
print(mock_agent_service.invoke.call_args[0])  # Positional args
print(mock_agent_service.invoke.call_args[1])  # Keyword args
```

---

## Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
- name: Run Integration Tests
  run: |
    poetry run pytest tests/integration/ \
      --cov=backend.deep_agent \
      --cov-report=xml \
      --cov-report=html \
      -v
```

### Coverage Requirements

```ini
# .coveragerc
[run]
source = backend.deep_agent
omit =
    */tests/*
    */migrations/*

[report]
fail_under = 80
```

---

## Common Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_operation(mock_settings):
    """Test async operation."""
    service = AgentService(settings=mock_settings)
    result = await service.invoke("Hello", "thread-123")
    assert result is not None
```

### Testing WebSocket Connections

```python
def test_websocket(client, mock_agent_service):
    """Test WebSocket communication."""
    with client.websocket_connect("/api/v1/ws") as websocket:
        # Send message
        websocket.send_json({"type": "chat", "message": "Hello", ...})

        # Receive response
        event = websocket.receive_json()
        assert "event" in event
```

### Testing SSE Streams

```python
def test_sse_stream(client, mock_agent_service):
    """Test Server-Sent Events."""
    with client.stream("POST", "/api/v1/chat/stream", json={...}) as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                # Process event
```

### Testing Error Handling

```python
def test_error_handling(client, mock_agent_service):
    """Test error handling."""
    # Mock service to raise error
    mock_agent_service.invoke.side_effect = ValueError("Invalid input")

    # Verify error handled gracefully
    response = client.post("/api/v1/chat", json={...})
    assert response.status_code == 400
```

---

## Best Practices Summary

1. **Focus on interactions** between components, not isolated units
2. **Mock external dependencies** only (APIs, MCP servers)
3. **Test real internal logic** (validation, routing, error handling)
4. **Use realistic test data** (real-world message content, thread IDs)
5. **Follow AAA pattern** (Arrange, Act, Assert)
6. **Document test scenarios** (what's being tested, why, expected behavior)
7. **Test both happy path and errors** (success + failure modes)
8. **Verify error propagation** across architectural boundaries
9. **Use descriptive test names** (`test_chat_endpoint_returns_valid_response`)
10. **Keep tests independent** (no shared state between tests)

---

**For questions or issues with integration tests, see:**
- Test strategy: `/docs/development/testing.md`
- Contributing guide: `/CONTRIBUTING.md`
- GitHub issues: Tag with `tests` label
