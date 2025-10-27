# API Endpoint Documentation

Deep Agent AGI provides a RESTful API built with FastAPI. This document describes all available endpoints, request/response formats, and error handling.

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Table of Contents

- [Health Check](#health-check)
- [Chat Endpoints](#chat-endpoints)
  - [POST /chat - Send Chat Message](#post-chat)
  - [POST /chat/stream - Streaming Chat](#post-chatstream)
- [Agent Endpoints](#agent-endpoints)
  - [GET /agents/{thread_id} - Get Agent Status](#get-agentsthread_id)
  - [POST /agents/{thread_id}/approve - HITL Approval](#post-agentsthread_idapprove)
- [WebSocket](#websocket)
  - [WS /ws - Real-time Events](#ws-ws)
- [Error Handling](#error-handling)

---

## Health Check

### GET /health

Check if the API is running and healthy.

**Response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

## Chat Endpoints

### POST /chat

Send a chat message to the agent and receive a complete response.

**Endpoint:** `/api/v1/chat`

**Request Body:**

```json
{
  "message": "Hello, how can you help me?",
  "thread_id": "user-thread-123",
  "metadata": {
    "user_id": "user-456",
    "source": "web"
  }
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message (1-10000 chars) |
| `thread_id` | string | Yes | Conversation thread ID |
| `metadata` | object | No | Additional context metadata |

**Response:**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how can you help me?",
      "timestamp": "2025-01-27T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "I'm a helpful AI assistant. I can help you with various tasks including...",
      "timestamp": "2025-01-27T10:30:02Z"
    }
  ],
  "thread_id": "user-thread-123",
  "status": "success",
  "metadata": {
    "tokens_used": 150,
    "reasoning_effort": "medium",
    "tools_called": []
  }
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `messages` | array | List of messages in conversation |
| `thread_id` | string | Conversation thread ID |
| `status` | string | `success`, `error`, or `interrupted` |
| `metadata` | object | Response metadata (tokens, tools, etc.) |

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you do?",
    "thread_id": "test-001"
  }'
```

---

### POST /chat/stream

Send a chat message and receive streaming Server-Sent Events (SSE).

**Endpoint:** `/api/v1/chat/stream`

**Request Body:** Same as `/chat`

**Response:** Server-Sent Events (text/event-stream)

**Event Types:**

#### 1. RunStarted

Agent run begins.

```
event: RunStarted
data: {"run_id": "run-123", "thread_id": "thread-001", "timestamp": "2025-01-27T10:30:00Z"}
```

#### 2. TextMessageStart

Assistant message begins.

```
event: TextMessageStart
data: {"message_id": "msg-456", "role": "assistant"}
```

#### 3. TextMessageContent

Message content chunk (streaming).

```
event: TextMessageContent
data: {"content": "I can help you with "}
```

#### 4. TextMessageEnd

Assistant message complete.

```
event: TextMessageEnd
data: {"message_id": "msg-456", "complete": true}
```

#### 5. ToolCallStart

Agent begins tool execution.

```
event: ToolCallStart
data: {"tool_id": "call-789", "tool_name": "web_search"}
```

#### 6. ToolCallArgs

Tool call arguments.

```
event: ToolCallArgs
data: {"tool_id": "call-789", "args": {"query": "Python latest news"}}
```

#### 7. ToolCallResult

Tool execution result.

```
event: ToolCallResult
data: {"tool_id": "call-789", "result": "Search results: ..."}
```

#### 8. StepFinished

Agent step complete.

```
event: StepFinished
data: {"step": 1, "status": "completed"}
```

#### 9. RunFinished

Agent run complete.

```
event: RunFinished
data: {"run_id": "run-123", "status": "success", "tokens_used": 200}
```

#### 10. RunError

Agent encountered an error.

```
event: RunError
data: {"run_id": "run-123", "error": "Rate limit exceeded", "code": "rate_limit_error"}
```

**Example:**

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Search for Python news",
    "thread_id": "test-stream-001"
  }'
```

**JavaScript Client:**

```javascript
const eventSource = new EventSource('/api/v1/chat/stream?message=Hello&thread_id=test-001');

eventSource.addEventListener('TextMessageContent', (event) => {
  const data = JSON.parse(event.data);
  console.log('Content:', data.content);
});

eventSource.addEventListener('RunFinished', (event) => {
  const data = JSON.parse(event.data);
  console.log('Run finished:', data.status);
  eventSource.close();
});
```

---

## Agent Endpoints

### GET /agents/{thread_id}

Get the current status of an agent thread.

**Endpoint:** `/api/v1/agents/{thread_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `thread_id` | string | Thread ID to query |

**Response:**

```json
{
  "thread_id": "thread-001",
  "status": "running",
  "current_state": {
    "messages": [...],
    "next": ["tool_execution"],
    "checkpoint_id": "checkpoint-abc123"
  },
  "metadata": {
    "created_at": "2025-01-27T10:30:00Z",
    "last_updated": "2025-01-27T10:30:05Z"
  }
}
```

**Status Values:**
- `idle` - No active run
- `running` - Agent is processing
- `interrupted` - Waiting for HITL approval
- `completed` - Run finished
- `error` - Error occurred

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Thread not found

**Example:**

```bash
curl http://localhost:8000/api/v1/agents/thread-001
```

---

### POST /agents/{thread_id}/approve

Submit Human-in-the-Loop (HITL) approval decision.

**Endpoint:** `/api/v1/agents/{thread_id}/approve`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `thread_id` | string | Thread ID |

**Request Body:**

```json
{
  "action": "approve",
  "message": "Approved by user"
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | `approve`, `reject`, or `respond` |
| `message` | string | No | Optional message from user |

**Response:**

```json
{
  "status": "approved",
  "thread_id": "thread-001",
  "continued": true,
  "message": "Agent will continue execution"
}
```

**Status Codes:**
- `200 OK` - Approval processed
- `400 Bad Request` - Invalid action
- `404 Not Found` - Thread not found
- `422 Unprocessable Entity` - Validation error

**Example - Approve:**

```bash
curl -X POST http://localhost:8000/api/v1/agents/thread-001/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "message": "Looks good, proceed"
  }'
```

**Example - Reject:**

```bash
curl -X POST http://localhost:8000/api/v1/agents/thread-001/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "message": "Too risky, please stop"
  }'
```

**Example - Custom Response:**

```bash
curl -X POST http://localhost:8000/api/v1/agents/thread-001/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action": "respond",
    "message": "Instead of deleting, please archive the files"
  }'
```

---

## WebSocket

### WS /ws

Establish a WebSocket connection for real-time bidirectional communication.

**Endpoint:** `ws://localhost:8000/ws`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | string | Yes | Conversation thread ID |

**Connection:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?thread_id=thread-001');
```

**Client → Server Messages:**

```json
{
  "type": "message",
  "content": "Hello from client",
  "metadata": {
    "user_id": "user-123"
  }
}
```

**Server → Client Events:**

Same event types as `/chat/stream`:
- `RunStarted`
- `TextMessageContent`
- `ToolCallStart`
- `RunFinished`
- etc.

**Example:**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?thread_id=my-thread');

ws.onopen = () => {
  console.log('Connected');

  // Send message
  ws.send(JSON.stringify({
    type: 'message',
    content: 'Hello, agent!'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

**Connection Management:**

- **Heartbeat:** Server sends ping every 30s
- **Timeout:** Client should pong within 60s
- **Reconnection:** Client should implement exponential backoff

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Error message here",
  "error_code": "validation_error",
  "timestamp": "2025-01-27T10:30:00Z",
  "request_id": "req-abc123"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 422 | Invalid input data |
| `rate_limit_error` | 429 | Too many requests |
| `authentication_error` | 401 | Invalid API key |
| `not_found_error` | 404 | Resource not found |
| `internal_error` | 500 | Server error |
| `agent_error` | 500 | Agent execution error |
| `timeout_error` | 504 | Request timeout |

### Rate Limiting

- **Default Limit:** 100 requests per minute per IP
- **Headers:**
  - `X-RateLimit-Limit` - Max requests per window
  - `X-RateLimit-Remaining` - Remaining requests
  - `X-RateLimit-Reset` - Reset timestamp

**Example Rate Limit Response:**

```json
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706353860

{
  "detail": "Rate limit exceeded. Try again in 30 seconds.",
  "error_code": "rate_limit_error"
}
```

### Request IDs

All responses include `X-Request-ID` header for tracing:

```
X-Request-ID: req-abc123def456
```

Use this ID when reporting issues or debugging.

---

## Authentication

**Phase 0:** No authentication required (development only).

**Phase 1+:** OAuth 2.0 Bearer token authentication:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "thread_id": "thread-001"}'
```

---

## CORS

Allowed origins configured via `ALLOWED_ORIGINS` environment variable:

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Allowed Methods:** GET, POST, PUT, DELETE, OPTIONS
**Allowed Headers:** Content-Type, Authorization, X-Request-ID

---

## Pagination

**Phase 1+:** List endpoints support pagination:

```bash
GET /api/v1/threads?page=1&page_size=20
```

**Response:**

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

---

## Versioning

API version is included in URL: `/api/v1/`

**Current Version:** v1
**Deprecation Notice:** 6 months before breaking changes

---

## SDKs & Libraries

**Python SDK** (Phase 1+):

```python
from deep_agent_sdk import DeepAgentClient

client = DeepAgentClient(api_key="your_key")
response = client.chat.send(
    message="Hello",
    thread_id="thread-001"
)
```

**JavaScript SDK** (Phase 1+):

```javascript
import { DeepAgentClient } from '@deep-agent/sdk';

const client = new DeepAgentClient({ apiKey: 'your_key' });
const response = await client.chat.send({
  message: 'Hello',
  threadId: 'thread-001'
});
```

---

## Additional Resources

- **OpenAPI Spec:** http://localhost:8000/openapi.json
- **Setup Guide:** [docs/development/setup.md](../development/setup.md)
- **Testing Guide:** [docs/development/testing.md](../development/testing.md)
- **Architecture:** README.md

---

## Support

- **Issues:** https://github.com/yourusername/deep-agent-agi/issues
- **Discussions:** https://github.com/yourusername/deep-agent-agi/discussions
- **Email:** support@deep-agent-agi.com (Phase 1+)
