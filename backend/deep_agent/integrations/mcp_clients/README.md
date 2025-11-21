# MCP Clients

## Purpose

Model Context Protocol (MCP) client implementations for external services integration. MCP provides a standardized interface for agents to communicate with external tools, APIs, and data sources.

This module enables the Deep Agent framework to:
- Perform web searches via Perplexity AI
- Retrieve real-time information from external sources
- Integrate with specialized APIs using a unified protocol
- Handle external service communication with built-in retry logic and error handling

## Key Files

- `__init__.py` - Module exports and package-level documentation
- `perplexity.py` - Perplexity web search client with rate limiting and security features

## Architecture

### MCP Protocol Overview

Model Context Protocol standardizes agent-to-service communication:

1. **Stdio Transport**: MCP servers run as separate processes, communicating via stdin/stdout
2. **Session Management**: ClientSession handles connection lifecycle and tool invocation
3. **Tool Invocation**: Agents call named tools with typed arguments
4. **Response Format**: Structured responses with content, metadata, and error handling

```
┌─────────────┐         ┌──────────────┐         ┌──────────────────┐
│   Agent     │ ◄─────► │ MCP Client   │ ◄─────► │  MCP Server      │
│  (Python)   │  async  │ (this module)│  stdio  │ (External)       │
└─────────────┘         └──────────────┘         └──────────────────┘
```

### Design Patterns

- **Async/Await**: All MCP calls use async patterns for non-blocking I/O
- **Retry Logic**: Exponential backoff for transient failures (tenacity)
- **Rate Limiting**: In-memory request throttling (Phase 0), Redis-based for production
- **Security**: Query sanitization, API key masking, timeout enforcement
- **Error Handling**: Structured exceptions with context for debugging

## Usage

### Perplexity Web Search

```python
from deep_agent.integrations.mcp_clients import PerplexityClient

# Initialize client
client = PerplexityClient()

# Perform search
results = await client.search(
    query="AI agent frameworks 2025",
    max_results=5
)

# Format results for agent consumption
formatted = client.format_results_for_agent(results)
print(formatted)

# Extract source URLs
sources = client.extract_sources(results)
print(f"Found {len(sources)} sources")
```

### Custom Settings

```python
from deep_agent.config.settings import get_settings

settings = get_settings()
settings.PERPLEXITY_API_KEY = "your-key-here"
settings.MCP_PERPLEXITY_TIMEOUT = 30  # seconds

client = PerplexityClient(settings=settings)
```

### Error Handling

```python
try:
    results = await client.search("quantum computing")
except ValueError as e:
    # Invalid query or response format
    print(f"Validation error: {e}")
except ConnectionError as e:
    # MCP server connection failed
    print(f"Connection error: {e}")
except TimeoutError as e:
    # Request exceeded timeout
    print(f"Timeout: {e}")
except RuntimeError as e:
    # API error (e.g., rate limit exceeded)
    print(f"Runtime error: {e}")
```

## MCP Protocol Details

### Server Configuration

MCP servers are configured via `.mcp/` directory:

```json
// .mcp/perplexity.json
{
  "command": "python",
  "args": ["-m", "perplexity_mcp"],
  "env": {
    "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
    "PERPLEXITY_MODEL": "sonar"
  }
}
```

### Tool Invocation

MCP clients invoke tools using structured arguments:

```python
result = await session.call_tool(
    name="perplexity_search_web",
    arguments={
        "query": "climate change impacts",
        "recency": "month"  # Last 30 days
    }
)
```

### Response Parsing

Perplexity MCP returns text with citations:

```
<main content with AI-generated summary>

Citations:
[1] https://example.com/source1
[2] https://example.com/source2
```

The client parses this into structured results:

```python
{
    "results": [
        {
            "title": "Perplexity Search: climate change impacts",
            "url": "https://example.com/source1",
            "snippet": "<main content>",
            "relevance_score": 1.0
        }
    ],
    "query": "climate change impacts",
    "sources": 2
}
```

## Security Features

### Rate Limiting

- **In-Memory Throttling** (Phase 0): Thread-safe sliding window
- **Limits**: 10 requests per 60 seconds (configurable)
- **Enforcement**: RuntimeError raised when exceeded

### Query Sanitization

- **Character Filtering**: Removes potentially dangerous characters
- **Length Limits**: Truncates queries to prevent DoS attacks
- **Regex Pattern**: `[^\w\s\-.,?!']` (alphanumeric + basic punctuation only)

### API Key Protection

- **Masked Logging**: API keys never logged in plain text
- **Environment Variables**: Keys stored in `.env` (not committed)
- **Validation**: Checks for presence before allowing requests

### Timeout Enforcement

- **Hard Limits**: `asyncio.timeout()` prevents hung requests
- **Configurable**: `MCP_PERPLEXITY_TIMEOUT` in settings
- **Default**: 30 seconds

## Dependencies

### External Libraries

- `mcp`: Model Context Protocol library for client/server communication
- `tenacity`: Retry logic with exponential backoff
- `asyncio`: Async/await support for non-blocking I/O

### Internal Dependencies

- `deep_agent.config.settings`: Configuration management
- `deep_agent.core.logging`: Structured logging
- `deep_agent.core.security`: API key masking utilities

## Testing

### Unit Tests

Located in `tests/unit/test_integrations/test_mcp_clients/`:

```bash
pytest tests/unit/test_integrations/test_mcp_clients/test_perplexity.py -v
```

**Test Coverage:**
- Client initialization and validation
- Search query validation (empty, malformed)
- Rate limiting enforcement
- Query sanitization (injection prevention)
- Response format validation
- Error handling (connection, timeout, API errors)
- Result formatting and source extraction

### Integration Tests

Located in `tests/integration/test_integrations/test_mcp_clients/`:

```bash
pytest tests/integration/test_integrations/test_mcp_clients/test_perplexity.py -v
```

**Test Coverage:**
- Actual MCP server communication (mocked)
- Tool invocation and response parsing
- Retry logic with transient failures
- Timeout enforcement with slow responses

### Live API Tests (Phase 0.5)

Located in `tests/live_api/`:

```bash
./scripts/test_live_api.sh
```

**Test Coverage:**
- Real Perplexity API calls (costs ~$0.10 per run)
- End-to-end workflow validation
- Citation parsing with real data

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Perplexity API
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Model selection
PERPLEXITY_MODEL=sonar  # Default: sonar

# Optional: Timeout (seconds)
MCP_PERPLEXITY_TIMEOUT=30  # Default: 30s
```

### Rate Limiting Configuration

```python
# In perplexity.py
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 10  # 10 requests per minute
```

**Phase 1 Enhancement**: Replace in-memory throttling with Redis-based rate limiting for distributed systems.

## Related Documentation

- [Parent Integration Module](../README.md) - Overview of all integrations
- [MCP Specification](https://modelcontextprotocol.io/) - Protocol documentation
- [Perplexity MCP GitHub](https://github.com/perplexityai/modelcontextprotocol) - Server implementation
- [Configuration Guide](../../config/README.md) - Settings and environment variables
- [Security Documentation](../../core/README.md) - Security best practices

## Future Enhancements (Phase 1+)

### Additional MCP Clients

- **Gmail MCP**: Email analysis and search
- **GitHub MCP**: Repository and issue integration
- **Calendar MCP**: Calendar management (Google Calendar, Outlook)
- **Database MCP**: Secure database query interfaces

### Production Features

- **Redis Rate Limiting**: Distributed rate limiting across instances
- **Circuit Breaker**: Auto-disable failing MCP servers
- **Metrics Collection**: Request latency, error rates, throughput
- **Caching**: Response caching for repeated queries
- **Load Balancing**: Multi-instance MCP server pools

### Security Enhancements

- **mTLS**: Mutual TLS for MCP server authentication
- **Token Rotation**: Automatic API key rotation
- **Audit Logging**: Comprehensive request/response logging
- **Input Validation**: Schema-based validation using Pydantic models

## Troubleshooting

### Common Issues

#### MCP Server Not Starting

**Symptom**: `ConnectionError: Failed to connect to Perplexity MCP`

**Solutions**:
1. Verify MCP server installed: `python -m perplexity_mcp --version`
2. Check API key in `.env`: `echo $PERPLEXITY_API_KEY`
3. Verify `.mcp/perplexity.json` configuration exists
4. Check logs: `tail -f logs/deep-agent.log`

#### Rate Limit Exceeded

**Symptom**: `RuntimeError: Rate limit exceeded: 10 requests per 60s`

**Solutions**:
1. Reduce query frequency in your application
2. Increase rate limits in `perplexity.py` (if justified)
3. Implement request queuing/batching
4. Upgrade to Redis-based rate limiting (Phase 1)

#### Query Sanitization Too Aggressive

**Symptom**: Special characters removed from queries

**Solutions**:
1. Review regex pattern in `_sanitize_query()`
2. Add specific characters to allowlist if safe
3. Log sanitized queries to verify behavior
4. Consider context-specific sanitization rules

#### Timeout Errors

**Symptom**: `TimeoutError: MCP request exceeded 30s timeout`

**Solutions**:
1. Increase `MCP_PERPLEXITY_TIMEOUT` in `.env`
2. Check network connectivity to Perplexity API
3. Verify MCP server performance
4. Review query complexity (simpler queries = faster responses)

## Contributing

When adding new MCP clients:

1. **Follow Patterns**: Use `perplexity.py` as a template
2. **Add Docstrings**: Google-style docstrings for all classes/methods
3. **Write Tests**: Unit + integration tests (80%+ coverage)
4. **Security First**: Sanitize inputs, mask secrets, enforce timeouts
5. **Error Handling**: Raise specific exceptions with context
6. **Logging**: Structured logs with correlation IDs
7. **Update README**: Document usage, configuration, troubleshooting

### New Client Checklist

- [ ] Client class with async methods
- [ ] Rate limiting (in-memory or Redis)
- [ ] Input sanitization and validation
- [ ] Timeout enforcement
- [ ] Retry logic with exponential backoff
- [ ] API key masking in logs
- [ ] Comprehensive docstrings
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] Configuration in `.env.example`
- [ ] MCP server config in `.mcp/`
- [ ] README section with usage examples
- [ ] Export in `__init__.py`

---

**Last Updated**: 2025-11-12
**Maintainer**: Deep Agent AGI Team
**Status**: Phase 0 Complete
