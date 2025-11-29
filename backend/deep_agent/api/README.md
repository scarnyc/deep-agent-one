# API

## Purpose
FastAPI application setup and route registration for Deep Agent One backend. Provides RESTful HTTP endpoints, Server-Sent Events (SSE) streaming, and WebSocket connections for real-time agent interaction.

## Key Files
- `__init__.py` - API package initialization with module docstrings
- `dependencies.py` - Dependency injection for AgentService (singleton pattern with FastAPI DI)
- `middleware.py` - Custom middleware (TimeoutMiddleware for request timeout protection)
- `v1/` - Version 1 API routes (chat, agents, WebSocket)

## Usage

### Starting the API
```bash
# Development mode with auto-reload
uvicorn deep_agent.main:app --reload --port 8000

# Production mode
uvicorn deep_agent.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Chat (synchronous)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What files are in my project?", "thread_id": "user-123"}'

# Chat stream (SSE)
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "What files are in my project?", "thread_id": "user-123"}'

# Get agent status
curl http://localhost:8000/api/v1/agents/user-123

# Approve HITL request
curl -X POST http://localhost:8000/api/v1/agents/user-123/approve \
  -H "Content-Type: application/json" \
  -d '{"run_id": "run-456", "thread_id": "user-123", "action": "accept"}'
```

## API Structure

### Health Endpoint
- `GET /health` - Health check endpoint (returns `{"status": "healthy"}`)

### V1 API Routes (`/api/v1/`)

#### Chat Endpoints (`v1/chat.py`)
- `POST /api/v1/chat` - Synchronous chat (returns complete response)
- `POST /api/v1/chat/stream` - Streaming chat via SSE (real-time events)

#### Agent Management Endpoints (`v1/agents.py`)
- `GET /api/v1/agents/{thread_id}` - Get agent run status
- `POST /api/v1/agents/{thread_id}/approve` - Approve HITL request
- `POST /api/v1/agents/{thread_id}/respond` - Respond to HITL with custom text

#### WebSocket Endpoint (`v1/websocket.py`)
- `WS /api/v1/ws` - WebSocket connection for real-time bidirectional streaming
  - Supports chat messages, agent events, HITL approvals, and cancellation

## Dependencies

### Internal Dependencies
- `../services/agent_service.py` - Core agent execution logic (LangGraph agents)
- `../models/` - Pydantic models for requests/responses
- `../core/logging.py` - Structured logging with context
- `../core/serialization.py` - Event serialization for streaming
- `../core/security.py` - Security utilities (error sanitization)

### External Dependencies
- `fastapi` - Web framework with OpenAPI support
- `uvicorn` - ASGI server for FastAPI
- `slowapi` - Rate limiting middleware
- `python-multipart` - Form data parsing (optional)
- `websockets` - WebSocket support

## Architecture

### Dependency Injection Pattern
The API uses FastAPI's dependency injection system to provide AgentService to endpoints:

```python
from deep_agent.api.dependencies import AgentServiceDep

@router.post("/chat")
async def chat(request: ChatRequest, service: AgentServiceDep):
    result = await service.invoke(request.message, request.thread_id)
    return result
```

**Benefits:**
- Easy testing with `app.dependency_overrides`
- Singleton pattern prevents expensive re-initialization
- Separation of concerns (routes don't create services)

### Middleware Stack
1. **TimeoutMiddleware** - Enforces 30s request timeout (configurable)
2. **CORS Middleware** - Configured for frontend origin (localhost:3000)
3. **Request ID Middleware** - Adds unique ID to each request for tracing

### Rate Limiting
All endpoints use `slowapi` for rate limiting:
- Chat endpoints: 10 requests/minute per IP
- Agent status: 30 requests/minute per IP
- HITL approval: 10 requests/minute per IP

### Error Handling
- Validation errors (422): Raised before processing
- Runtime errors (500): Logged with sanitized messages
- WebSocket errors: Sent as error events in stream

## Related Documentation
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [Services](../services/README.md) - AgentService implementation
- [API v1](v1/README.md) - Detailed v1 endpoint documentation
- [Models](../models/README.md) - Request/response schemas
- [WebSocket Protocol](v1/websocket.py) - WebSocket event format

## Testing
- Unit tests: `tests/unit/test_api/` - Route handler logic
- Integration tests: `tests/integration/test_api/` - Full API requests
- E2E tests: `tests/e2e/` - Complete workflows (chat → agent → response)

### Running Tests
```bash
# All API tests
pytest tests/unit/test_api/ tests/integration/test_api/ -v

# With coverage
pytest tests/unit/test_api/ tests/integration/test_api/ --cov=deep_agent.api

# Specific endpoint
pytest tests/integration/test_api/test_chat.py::test_chat_endpoint -v
```

## Development Notes

### Phase 0 Implementation Status
- ✅ Core endpoints (chat, agents, WebSocket)
- ✅ Rate limiting with slowapi
- ✅ Timeout middleware
- ✅ Dependency injection
- ✅ Structured logging
- ✅ Error handling with sanitization
- ✅ SSE streaming support
- ✅ WebSocket bidirectional streaming
- ✅ HITL approval workflows

### Phase 1 Enhancements (Planned)
- [ ] Authentication & authorization (OAuth 2.0)
- [ ] User-specific rate limits (Redis-backed)
- [ ] Advanced WebSocket features (reconnection, progress events)
- [ ] Request tracing with LangSmith integration
- [ ] API versioning strategy (v2 endpoints)
- [ ] OpenAPI schema customization

### Known Issues
See `GITHUB_ISSUES.md` for tracked issues and technical debt.

## Security Considerations

### Phase 0 Security Features
- Request timeout protection (30s default)
- Rate limiting per IP
- Error message sanitization (no stack traces to clients)
- Input validation with Pydantic
- CORS restrictions

### Phase 1 Security Enhancements
- [ ] JWT-based authentication
- [ ] API key management
- [ ] Request signature verification
- [ ] Advanced rate limiting (per user, per endpoint)
- [ ] Audit logging for sensitive operations
- [ ] WAF integration (Cloudflare)

## Performance Considerations

### Current Implementation
- Singleton AgentService (avoids re-initialization overhead)
- Async/await throughout (non-blocking I/O)
- Streaming responses (SSE, WebSocket) for better UX
- Connection pooling for database (PostgreSQL)

### Phase 1 Optimizations
- [ ] Response caching (Redis)
- [ ] Database query optimization
- [ ] Load balancing (Nginx, cloud-native)
- [ ] CDN for static assets
- [ ] Compression middleware

## API Versioning Strategy

### Current: v1 (Phase 0)
All endpoints under `/api/v1/` prefix. No breaking changes expected during Phase 0.

### Future: v2 (Phase 1+)
When introducing breaking changes:
1. Create `api/v2/` directory
2. Mount v2 routes under `/api/v2/`
3. Maintain v1 for backward compatibility (6-12 months)
4. Document migration guide
5. Add deprecation warnings to v1 responses

### Deprecation Process
1. Announce deprecation (release notes, docs, API response headers)
2. Provide migration guide with code examples
3. Set sunset date (6-12 months out)
4. Add `X-API-Deprecation` header to deprecated endpoints
5. Monitor usage metrics
6. Remove after sunset date

## Monitoring & Observability

### Current (Phase 0)
- Structured logging with context (request_id, thread_id, etc.)
- FastAPI built-in metrics (request count, latency)
- Health check endpoint for uptime monitoring

### Phase 1 Enhancements
- [ ] LangSmith integration for agent tracing
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] APM integration (Datadog, New Relic)
- [ ] Error tracking (Sentry)
- [ ] Custom business metrics (chat completion rate, HITL approval time)

## Contributing

### Adding New Endpoints
1. Create route handler in appropriate module (`v1/chat.py`, `v1/agents.py`, etc.)
2. Add Pydantic models in `models/` directory
3. Add comprehensive docstrings (Google style)
4. Add rate limiting decorator
5. Add error handling
6. Write tests (unit + integration)
7. Update this README
8. Run code-review-expert before committing

### Code Style
- Follow PEP 8 (enforced by Ruff)
- Use type hints (enforced by mypy)
- Google-style docstrings
- Async/await for all I/O operations

## License
See project root LICENSE file.
