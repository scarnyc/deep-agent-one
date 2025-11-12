# API Documentation

## Purpose
API reference documentation, endpoint specifications, and integration guides for the Deep Agent AGI backend.

## Contents

### Current Documentation
- [API Endpoints](endpoints.md) - REST and WebSocket endpoint specifications

### Planned Documentation (Phase 1+)
- OpenAPI/Swagger specification
- Code examples (Python, JavaScript, cURL)
- Rate limiting documentation
- WebSocket protocol detailed specification
- AG-UI Protocol implementation guide
- Authentication and authorization
- Error codes and handling

## Quick Links
- [Backend API Code](../../backend/deep_agent/api/)
- [API Models](../../backend/deep_agent/models/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Implementation](../development/websocket.md)

## API Overview

### Base URL
- **Development:** `http://localhost:8000`
- **Staging:** TBD
- **Production:** TBD

### API Types
1. **REST API:** Standard HTTP endpoints for chat and agent operations
2. **WebSocket API:** Real-time streaming for agent execution and events

### Authentication
- **Phase 0:** No authentication (development only)
- **Phase 1:** OAuth 2.0, rotating credentials, least-privilege access

## REST API

### Health Check
```
GET /health
```
Returns API health status.

### Chat Endpoints
```
POST /api/chat
POST /api/chat/stream
```
Send chat messages and receive responses (streaming or non-streaming).

See [endpoints.md](endpoints.md) for detailed specifications.

## WebSocket API

### Connection
```
ws://localhost:8000/ws/agents/{thread_id}
```

### AG-UI Protocol Events
The WebSocket API implements the AG-UI Protocol for real-time agent event streaming:

#### Lifecycle Events
- `RunStarted` - Agent execution begins
- `RunFinished` - Agent execution completes
- `RunError` - Agent execution error
- `StepStarted` - Agent step begins
- `StepFinished` - Agent step completes

#### Message Events
- `TextMessageStart` - Text message begins
- `TextMessageContent` - Text message chunk
- `TextMessageEnd` - Text message completes

#### Tool Events
- `ToolCallStart` - Tool execution begins
- `ToolCallArgs` - Tool arguments
- `ToolCallEnd` - Tool execution completes
- `ToolCallResult` - Tool execution result

#### HITL Events
- Custom events for human-in-the-loop approval workflows

See [endpoints.md](endpoints.md) and [websocket.md](../development/websocket.md) for details.

## Generating API Documentation

API documentation can be accessed via FastAPI's automatic documentation:

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Spec (JSON):** http://localhost:8000/openapi.json

### Generating Static Docs
```bash
# Export OpenAPI spec
curl http://localhost:8000/openapi.json > docs/api/openapi.json

# Generate HTML docs (planned)
# redoc-cli bundle openapi.json -o api-docs.html
```

## Request/Response Formats

### Content Types
- **Request:** `application/json`
- **Response:** `application/json`
- **WebSocket:** JSON-encoded AG-UI Protocol events

### Standard Response Structure
```json
{
  "status": "success" | "error",
  "data": { /* response data */ },
  "error": { /* error details if status=error */ }
}
```

### Error Response Structure
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* optional error details */ }
  }
}
```

## Rate Limiting

### Phase 0 (Development)
- No rate limiting

### Phase 1+ (Production)
- Rate limiting implemented via `slowapi`
- Limits TBD based on tier/plan
- Rate limit headers:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Error Codes

### HTTP Status Codes
- `200 OK` - Success
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required (Phase 1+)
- `403 Forbidden` - Insufficient permissions (Phase 1+)
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded (Phase 1+)
- `500 Internal Server Error` - Server error

### Application Error Codes
```
VALIDATION_ERROR - Request validation failed
AGENT_ERROR - Agent execution error
TOOL_ERROR - Tool execution error
TIMEOUT_ERROR - Operation timeout
WEBSOCKET_ERROR - WebSocket connection error
```

See [endpoints.md](endpoints.md) for complete error code reference.

## Code Examples

### Python Client Example
```python
import requests

# Chat completion
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "Hello, agent!",
        "thread_id": "user-123"
    }
)
print(response.json())
```

### JavaScript Client Example
```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/agents/user-123');

ws.onmessage = (event) => {
  const agEvent = JSON.parse(event.data);
  console.log('AG-UI Event:', agEvent);
};

ws.send(JSON.stringify({
  type: 'user_message',
  content: 'Hello, agent!'
}));
```

### cURL Examples
```bash
# Health check
curl http://localhost:8000/health

# Chat completion
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, agent!", "thread_id": "user-123"}'

# Streaming chat
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, agent!", "thread_id": "user-123"}' \
  --no-buffer
```

## WebSocket Client Libraries

### Python
- `websockets` library
- `socketio` for Socket.IO (if implemented)

### JavaScript/TypeScript
- Native WebSocket API
- `socket.io-client` for Socket.IO (if implemented)
- AG-UI React hooks

### Testing
- `pytest-asyncio` for async tests
- Playwright MCP for UI testing

## API Versioning

### Phase 0
- No versioning (development)

### Phase 1+
- URL-based versioning: `/api/v1/chat`
- Version in headers: `API-Version: 1`

## Related Documentation
- [Development](../development/)
- [Architecture](../architecture/)
- [WebSocket Implementation](../development/websocket.md)
- [AG-UI Protocol](https://docs.ag-ui.com/sdk/python/core/overview)

## Contributing to API Documentation

When adding or modifying API endpoints:
1. Update OpenAPI schema in FastAPI route decorators
2. Add/update endpoint documentation in [endpoints.md](endpoints.md)
3. Include request/response examples
4. Document error cases
5. Update this README if adding new API categories
6. Test all examples in documentation
