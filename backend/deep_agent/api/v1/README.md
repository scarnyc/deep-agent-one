# API v1

## Purpose

Version 1 API endpoints for Deep Agent AGI. Implements RESTful and WebSocket routes for agent interactions, providing both synchronous request/response and real-time streaming communication.

## Key Files

### `__init__.py`
Router registration module. Imports and exposes all v1 routers for inclusion in the FastAPI app.

### `chat.py`
Chat API endpoints for synchronous and streaming agent communication.

**Endpoints:**
- `POST /api/v1/chat` - Synchronous chat (request/response)
- `POST /api/v1/chat/stream` - Streaming chat (SSE)

**Features:**
- Rate limiting (10 requests/minute per IP)
- Structured logging with request IDs
- LangChain message format conversion
- Error sanitization for security
- SSE (Server-Sent Events) streaming support

### `agents.py`
Agent management API endpoints for HITL (Human-in-the-Loop) workflows.

**Endpoints:**
- `GET /api/v1/agents/{thread_id}` - Get agent run status
- `POST /api/v1/agents/{thread_id}/approve` - Approve/respond/edit HITL request
- `POST /api/v1/agents/{thread_id}/respond` - Convenience endpoint for RESPOND action

**Features:**
- Agent run status tracking
- HITL approval workflows (ACCEPT, RESPOND, EDIT)
- State management via LangGraph checkpointer
- Rate limiting (30/min for status, 10/min for approvals)

### WebSocket Endpoint (in `main.py`)
Real-time bidirectional communication for agent streaming.

**Endpoint:**
- `WS /api/v1/ws` - WebSocket for streaming agent responses

**Features:**
- AG-UI Protocol compatible events
- Graceful disconnect handling
- Event serialization (handles LangChain objects)
- Custom event filtering (processing_started)

---

## Endpoints

### REST Endpoints

#### POST /api/v1/chat
Synchronous chat endpoint for complete request/response.

**Request:**
```json
{
  "message": "What files are in my project?",
  "thread_id": "user-123",
  "metadata": {"source": "web", "user_id": "456"}
}
```

**Response:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What files are in my project?",
      "timestamp": "2025-01-01T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I found 15 files in your project...",
      "timestamp": "2025-01-01T12:00:05Z"
    }
  ],
  "thread_id": "user-123",
  "status": "success",
  "metadata": {"tokens": 250, "model": "gpt-5"},
  "trace_id": "trace-abc-123",
  "run_id": "run-def-456"
}
```

**Status Codes:**
- `200` - Success
- `422` - Validation error (invalid input)
- `429` - Rate limit exceeded
- `500` - Agent execution failed

---

#### POST /api/v1/chat/stream
Streaming chat endpoint using Server-Sent Events (SSE).

**Request:**
```json
{
  "message": "What files are in my project?",
  "thread_id": "user-123",
  "metadata": {"source": "web"}
}
```

**Response (SSE Stream):**
```
data: {"event_type": "on_chat_model_stream", "data": {"content": "I"}, "timestamp": "..."}

data: {"event_type": "on_chat_model_stream", "data": {"content": " found"}, "timestamp": "..."}

data: {"event_type": "on_tool_start", "data": {"tool": "read_file"}, "timestamp": "..."}

data: {"event_type": "on_tool_end", "data": {"output": "..."}, "timestamp": "..."}
```

**Event Types (AG-UI Protocol):**
- `on_chat_model_stream` - LLM token streaming
- `on_tool_start` - Tool execution started
- `on_tool_end` - Tool execution completed
- `on_chain_start` - Agent chain started
- `on_chain_end` - Agent chain completed
- `error` - Error occurred

**Status Codes:**
- `200` - Stream established
- `422` - Validation error before streaming starts
- Errors during streaming are sent as SSE events (not HTTP errors)

**Usage Example (JavaScript):**
```javascript
const eventSource = new EventSource('/api/v1/chat/stream', {
  method: 'POST',
  body: JSON.stringify({
    message: "What files are in my project?",
    thread_id: "user-123"
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.data);
};

eventSource.onerror = () => {
  console.error('SSE connection error');
  eventSource.close();
};
```

---

#### GET /api/v1/agents/{thread_id}
Get current agent run status for a conversation thread.

**Request:**
```bash
curl http://localhost:8000/api/v1/agents/user-123
```

**Response:**
```json
{
  "run_id": "checkpoint-abc-123",
  "thread_id": "user-123",
  "status": "running",
  "started_at": "2025-01-01T12:00:00Z",
  "completed_at": null,
  "trace_id": "trace-def-456",
  "metadata": {}
}
```

**Status Codes:**
- `200` - Success
- `404` - Thread not found
- `429` - Rate limit exceeded (30/min)
- `500` - Internal server error

---

#### POST /api/v1/agents/{thread_id}/approve
Approve, respond to, or edit an agent's HITL request.

**Request (ACCEPT action):**
```json
{
  "run_id": "run-456",
  "thread_id": "user-123",
  "action": "accept"
}
```

**Request (RESPOND action):**
```json
{
  "run_id": "run-456",
  "thread_id": "user-123",
  "action": "respond",
  "response_text": "Let me provide more context..."
}
```

**Request (EDIT action):**
```json
{
  "run_id": "run-456",
  "thread_id": "user-123",
  "action": "edit",
  "tool_edits": {
    "file_path": "/new/path/file.txt",
    "content": "Updated content"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Accept action processed successfully",
  "run_id": "run-456",
  "thread_id": "user-123",
  "updated_status": "running"
}
```

**Status Codes:**
- `200` - Success
- `400` - No pending HITL request
- `404` - Thread not found
- `422` - Validation error (missing required fields)
- `429` - Rate limit exceeded (10/min)
- `500` - Internal server error

---

#### POST /api/v1/agents/{thread_id}/respond
Convenience endpoint for RESPOND action (wraps `/approve` with validation).

**Request:**
```json
{
  "run_id": "run-456",
  "thread_id": "user-123",
  "action": "respond",
  "response_text": "Let me clarify the requirements..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Respond action processed successfully",
  "run_id": "run-456",
  "thread_id": "user-123",
  "updated_status": "running"
}
```

**Status Codes:**
- Same as `/approve` endpoint
- `422` - response_text is empty or missing

---

### WebSocket Endpoints

#### WS /api/v1/ws
WebSocket endpoint for real-time streaming agent communication.

**Protocol:**

**Client → Server (Message):**
```json
{
  "type": "chat",
  "message": "What files are in my project?",
  "thread_id": "user-123",
  "metadata": {"user_id": "456"}
}
```

**Server → Client (Events):**
```json
{
  "event": "on_chat_model_stream",
  "data": {"chunk": {"content": "I found"}},
  "request_id": "uuid-abc-123",
  "metadata": {"trace_id": "trace-def-456"}
}
```

**Server → Client (Errors):**
```json
{
  "event": "on_error",
  "data": {
    "error": "Agent execution failed",
    "error_type": "ValueError",
    "request_id": "uuid-abc-123"
  },
  "metadata": {
    "thread_id": "user-123",
    "connection_id": "conn-ghi-789"
  }
}
```

**Event Types (AG-UI Protocol):**
- `processing_started` - Custom event for cold start feedback (filter before AG-UI handler)
- `on_chat_model_stream` - LLM token streaming
- `on_tool_start` - Tool execution started
- `on_tool_end` - Tool execution completed
- `on_chain_start` - Agent chain started
- `on_chain_end` - Agent chain completed
- `on_error` - Error occurred

**Usage Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onopen = () => {
  console.log('Connected');
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Hello, agent!',
    thread_id: 'user-123'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Filter custom events before passing to AG-UI handler
  if (data.event === 'processing_started') {
    console.log('Agent initializing...');
    return; // Don't pass to AG-UI
  }

  // Pass to AG-UI event handler
  handleAgentEvent(data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Features:**
- Automatic disconnect detection and graceful cleanup
- Event serialization (handles LangChain/LangGraph objects)
- Request ID tracking for debugging
- Trace ID capture from events
- Connection ID logging

---

## Usage Examples

### cURL Examples

**Synchronous Chat:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What files are in my project?",
    "thread_id": "user-123"
  }'
```

**Streaming Chat (SSE):**
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What files are in my project?",
    "thread_id": "user-123"
  }'
```

**Get Agent Status:**
```bash
curl http://localhost:8000/api/v1/agents/user-123
```

**Approve HITL Request:**
```bash
curl -X POST http://localhost:8000/api/v1/agents/user-123/approve \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "run-456",
    "thread_id": "user-123",
    "action": "accept"
  }'
```

**Respond to HITL Request:**
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

---

## Request/Response Models

### Chat Models (from `models/chat.py`)

#### `ChatRequest`
```python
class ChatRequest(BaseModel):
    message: str              # User message (min_length=1)
    thread_id: str            # Thread identifier (min_length=1)
    metadata: dict[str, Any]  # Optional metadata (max 10KB, max depth 5)
```

#### `ChatResponse`
```python
class ChatResponse(BaseModel):
    messages: list[Message]   # Conversation messages (min_length=1)
    thread_id: str            # Thread identifier
    status: ResponseStatus    # SUCCESS, ERROR, PENDING
    metadata: dict[str, Any]  # Optional metadata
    error: str | None         # Error message if status=ERROR
    trace_id: str | None      # LangSmith trace ID
    run_id: str | None        # LangGraph checkpoint ID
```

#### `Message`
```python
class Message(BaseModel):
    role: MessageRole         # USER, ASSISTANT, SYSTEM
    content: str              # Message content (min_length=1)
    timestamp: datetime       # Auto-generated UTC timestamp
```

#### `StreamEvent`
```python
class StreamEvent(BaseModel):
    event_type: str           # Event type name (e.g., "on_chat_model_stream")
    data: dict[str, Any]      # Event payload
    timestamp: datetime       # Auto-generated UTC timestamp
    thread_id: str | None     # Optional thread identifier
```

---

### Agent Models (from `models/agents.py`)

#### `AgentRunInfo`
```python
class AgentRunInfo(BaseModel):
    run_id: str               # Unique run identifier
    thread_id: str            # Thread identifier
    status: AgentRunStatus    # RUNNING, COMPLETED, ERROR, INTERRUPTED
    started_at: datetime      # Start time (UTC)
    completed_at: datetime    # Completion time (None if running)
    error: str | None         # Error message if status=ERROR
    trace_id: str | None      # LangSmith trace ID
    metadata: dict[str, Any]  # Optional metadata
```

#### `HITLApprovalRequest`
```python
class HITLApprovalRequest(BaseModel):
    run_id: str               # Unique run identifier
    thread_id: str            # Thread identifier
    action: HITLAction        # ACCEPT, RESPOND, EDIT
    response_text: str        # Required for RESPOND action
    tool_edits: dict[str, Any] # Required for EDIT action
```

#### `HITLApprovalResponse`
```python
class HITLApprovalResponse(BaseModel):
    success: bool             # Whether action succeeded
    message: str              # Human-readable message
    run_id: str               # Unique run identifier
    thread_id: str            # Thread identifier
    updated_status: AgentRunStatus # New status (if changed)
```

#### `ErrorResponse`
```python
class ErrorResponse(BaseModel):
    error: str                # Human-readable error message
    detail: str | None        # Detailed error information
    thread_id: str | None     # Thread identifier
    trace_id: str | None      # LangSmith trace ID
    run_id: str | None        # LangGraph checkpoint ID
    request_id: str | None    # Request identifier
```

---

## Error Handling

### HTTP Status Codes

- **200** - Success
- **400** - Bad request (no pending HITL, invalid action)
- **404** - Resource not found (thread not found)
- **422** - Validation error (invalid input format)
- **429** - Rate limit exceeded
- **500** - Internal server error (agent execution failed)

### Error Response Format

**REST Endpoints:**
```json
{
  "detail": "Error message",
  "error_type": "ValueError",
  "context": {"additional": "info"}
}
```

**SSE Stream:**
```
data: {"event_type": "error", "data": {"error": "Error message", "status": "error"}}
```

**WebSocket:**
```json
{
  "event": "on_error",
  "data": {
    "error": "Error message",
    "error_type": "ValueError",
    "request_id": "uuid-abc-123"
  },
  "metadata": {
    "thread_id": "user-123",
    "connection_id": "conn-def-456"
  }
}
```

### Error Types

- **ValidationError** - Invalid input (422)
- **ValueError** - Validation logic error (400/422)
- **KeyError** - Missing required field
- **HTTPException** - FastAPI HTTP error
- **WebSocketDisconnect** - Client disconnected
- **DeepAgentError** - Custom agent error (500)
- **ConfigurationError** - Configuration issue

### Security Features

- **Error Sanitization:** Secrets (API keys, tokens) are redacted from error messages
- **Rate Limiting:** IP-based rate limiting on all endpoints
- **Input Validation:** Pydantic models validate all inputs
- **Metadata Size Limits:** Max 10KB, max 5 levels nesting
- **CORS:** Configurable origins with credential support
- **Request Timeouts:** 30s timeout middleware

---

## Dependencies

### Internal Dependencies

- **`../../services/agent_service.py`** - Agent invocation and streaming
- **`../../models/chat.py`** - Chat request/response models
- **`../../models/agents.py`** - Agent management models
- **`../../core/logging.py`** - Structured logging
- **`../../core/serialization.py`** - Event serialization (LangChain objects)
- **`../../core/security.py`** - Error message sanitization

### External Dependencies

- **`fastapi`** - Web framework
- **`pydantic`** - Data validation
- **`slowapi`** - Rate limiting middleware
- **`starlette`** - ASGI framework (used by FastAPI)
- **`websockets`** - WebSocket support (via FastAPI)
- **`uvicorn`** - ASGI server (for running the app)

---

## Related Documentation

- [API Root](../README.md) - API structure overview
- [Services](../../services/README.md) - AgentService implementation
- [Models](../../models/README.md) - Pydantic models
- [Core](../../core/README.md) - Logging, serialization, security
- [AG-UI Protocol](https://docs.ag-ui.com/sdk/python/core/overview) - Event types and protocol

---

## Testing

### Integration Tests

**Location:** `tests/integration/test_api/v1/`

**Test Files:**
- `test_chat_endpoint.py` - Chat endpoint tests
- `test_chat_stream_endpoint.py` - Streaming endpoint tests
- `test_agents_endpoint.py` - Agent management tests
- `test_websocket_endpoint.py` - WebSocket tests

**Run Tests:**
```bash
# All v1 API tests
pytest tests/integration/test_api/v1/ -v

# Specific endpoint
pytest tests/integration/test_api/v1/test_chat_endpoint.py -v

# With coverage
pytest tests/integration/test_api/v1/ --cov=deep_agent.api.v1 --cov-report=html
```

### Manual Testing

**Development Server:**
```bash
# Start server with auto-reload
./scripts/dev.sh

# Or with WebSocket support
./scripts/dev-ws.sh
```

**Interactive API Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**WebSocket Testing:**
```bash
# Using websocat
websocat ws://localhost:8000/api/v1/ws

# Send message (after connection)
{"type": "chat", "message": "Hello", "thread_id": "test-123"}
```

---

## Performance Considerations

### Rate Limiting

- **Chat endpoints:** 10 requests/minute per IP
- **Agent status:** 30 requests/minute per IP
- **Agent approval:** 10 requests/minute per IP

Adjust limits in endpoint decorators: `@limiter.limit("10/minute")`

### Streaming Performance

- **SSE:** Lower overhead, browser-native, one-way communication
- **WebSocket:** Bidirectional, more overhead, better for real-time interaction
- **Event Serialization:** LangChain objects converted to JSON-safe format

### Connection Management

- **WebSocket:** Long-lived connections with graceful disconnect handling
- **SSE:** HTTP streaming with automatic reconnection (client-side)
- **Request Timeouts:** 30s timeout for all HTTP requests

### Monitoring

- **LangSmith Traces:** All agent runs traced with `trace_id`
- **Request IDs:** Unique ID per request for debugging
- **Structured Logging:** JSON logs with context (request_id, thread_id, trace_id)

---

## Migration Notes (Phase 0 → Phase 1)

### Phase 1 Enhancements

1. **Authentication & Authorization**
   - Add JWT token validation middleware
   - User-specific rate limiting (by user_id, not IP)
   - Role-based access control (RBAC)

2. **Advanced HITL Workflows**
   - Multi-step approvals
   - Conditional branching
   - Approval history tracking

3. **Provenance Store Integration**
   - Source tracking for agent responses
   - Citation metadata in responses
   - Confidence scores

4. **WebSocket Reliability**
   - Proactive disconnect monitoring
   - Progress events for long-running tools
   - Reconnection logic with state recovery

5. **Custom TypeScript Components**
   - Replace AG-UI SDK with custom components
   - Advanced event visualizers
   - Custom HITL UI workflows

### Breaking Changes (None for Phase 0 → Phase 1)

Phase 1 enhancements will be additive and backward-compatible.

---

## Troubleshooting

### Common Issues

**1. Rate Limit Exceeded (429)**
- **Cause:** Too many requests from same IP
- **Solution:** Wait for rate limit window to reset or adjust limits in code

**2. WebSocket Disconnects Unexpectedly**
- **Cause:** Network hiccups, idle timeout, or server restart
- **Solution:** Implement reconnection logic in client

**3. SSE Stream Hangs**
- **Cause:** Nginx buffering or proxy timeout
- **Solution:** Add `X-Accel-Buffering: no` header (already included)

**4. Validation Errors (422)**
- **Cause:** Invalid input format
- **Solution:** Check request matches Pydantic model schema

**5. Agent Execution Fails (500)**
- **Cause:** LLM API error, tool failure, or configuration issue
- **Solution:** Check logs for `trace_id` and inspect in LangSmith

### Debug Tips

**Enable Debug Logging:**
```bash
ENV=dev DEBUG=true uvicorn deep_agent.main:app --reload
```

**Check Request ID:**
```bash
curl -v http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "thread_id": "debug-123"}'

# Response header: X-Request-ID: <uuid>
```

**Inspect Trace in LangSmith:**
```python
# In logs, find:
# "trace_id": "abc-123-def"

# Visit:
# https://smith.langchain.com/o/<org>/projects/p/<project>/r/<trace_id>
```

**Monitor WebSocket Events:**
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event, 'Data:', data.data);
};
```

---

## Contributing

When adding new endpoints:

1. **Add route in appropriate file** (`chat.py` or `agents.py`)
2. **Add Pydantic models** in `models/` directory
3. **Add docstrings** (Google-style)
4. **Add rate limiting** (`@limiter.limit()`)
5. **Add structured logging** (with `request_id`, `thread_id`, etc.)
6. **Add error handling** (with sanitization)
7. **Add integration tests** in `tests/integration/test_api/v1/`
8. **Update this README** with endpoint documentation

Example:
```python
@router.post("/new-endpoint", response_model=ResponseModel)
@limiter.limit("10/minute")
async def new_endpoint(
    request_body: RequestModel,
    request: Request,
) -> ResponseModel:
    """
    New endpoint description.

    Args:
        request_body: Request model
        request: FastAPI request object

    Returns:
        Response model

    Raises:
        HTTPException: 422 if validation fails
        HTTPException: 500 if execution fails
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info("New endpoint called", request_id=request_id)

    # Implementation here

    return response
```

---

## License

See [LICENSE](../../../../LICENSE) in project root.
