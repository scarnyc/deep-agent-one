# Integrations

## Purpose

External service integrations including LangSmith tracing, Opik prompt optimization, and Model Context Protocol (MCP) clients for extending agent capabilities.

This module bridges the Deep Agent framework with external services:
- **LangSmith**: Agent tracing, observability, and debugging
- **Opik**: Prompt optimization and A/B testing (Phase 1)
- **MCP Clients**: Web search, data retrieval, and external tools

## Key Files

### Core Integration Files
- `__init__.py` - Lazy loading for optional dependencies (Phase 1)
- `langsmith.py` - LangSmith tracing setup and configuration
- `opik_client.py` - Opik prompt optimization client with 6 algorithms
- `mcp_clients/` - Model Context Protocol client implementations

### MCP Clients
- `mcp_clients/__init__.py` - MCP client module exports
- `mcp_clients/perplexity.py` - Perplexity web search MCP client

## Lazy Loading Pattern

Phase 1 dependencies (Opik) use lazy imports to prevent blocking Phase 0 startup when optional packages are not installed. This allows the framework to gracefully handle missing dependencies.

**How it works:**

```python
# Phase 0 - Immediate imports (required)
from deep_agent.integrations import setup_langsmith
setup_langsmith()  # Works immediately

# Phase 1 - Lazy imports (optional)
from deep_agent.integrations import OpikClient
# ☝️ Import only triggers when OpikClient is accessed
# If opik/opik-optimizer not installed, raises ImportError here

client = OpikClient()  # Fails gracefully if package missing
```

**Implementation:**

The `__getattr__` function in `__init__.py` intercepts attribute access and loads Opik dependencies on-demand:

```python
def __getattr__(name):
    if name in ("OpikClient", "OptimizerAlgorithm", ...):
        # Lazy import happens here
        from deep_agent.integrations.opik_client import OpikClient
        return OpikClient
    raise AttributeError(f"module has no attribute {name!r}")
```

**Benefits:**
- Phase 0 works without installing Phase 1 packages
- Faster startup time (fewer imports at module load)
- Clear separation between required and optional dependencies
- Graceful degradation when optional features unavailable

## Usage

### LangSmith Tracing

Enable automatic tracing for all agent operations, LLM calls, and tool invocations:

```python
from deep_agent.integrations import setup_langsmith

# Configure LangSmith tracing (reads from environment)
setup_langsmith()

# All subsequent agent operations are traced automatically
# No manual instrumentation needed
```

**What gets traced:**
- Agent execution (state changes, decisions, HITL approvals)
- LLM calls (prompts, completions, tokens, reasoning effort)
- Tool invocations (name, arguments, results, errors)
- Performance metrics (latency, token usage, cost)
- Error states and stack traces

**Environment variables required:**
```bash
LANGSMITH_API_KEY=lsv2_xxx...
LANGSMITH_PROJECT=deep-agent-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_V2=true
```

### Opik Optimization (Phase 1)

Optimize prompts using 6 different algorithms with automated A/B testing:

```python
from deep_agent.integrations import OpikClient, OptimizerAlgorithm

# Initialize client (lazy loaded)
client = OpikClient()

# Create evaluation dataset
dataset = client.get_or_create_dataset(
    name="chat_eval",
    items=[
        {"input": "Hello", "expected_output": "Hi there!"},
        {"input": "How are you?", "expected_output": "I'm doing well!"},
    ]
)

# Define evaluation metric
def accuracy_metric(output, expected):
    return 1.0 if output.strip() == expected.strip() else 0.0

# Optimize prompt with Hierarchical Reflective algorithm (Rank #1)
result = await client.optimize_prompt_async(
    prompt="You are a helpful assistant.",
    dataset=dataset,
    metric=accuracy_metric,
    algorithm=OptimizerAlgorithm.HIERARCHICAL_REFLECTIVE,
    max_trials=10,
    model="gpt-4o"
)

print(f"Original: {result['original_prompt']}")
print(f"Optimized: {result['optimized_prompt']}")
print(f"Score: {result['score']:.2f}")
print(f"Improvement: {result['improvement']:.2f}%")
```

**Available algorithms:**

1. **HierarchicalReflectiveOptimizer** (Rank #1, 67.83%) - Best for complex prompts
2. **FewShotBayesianOptimizer** (Rank #2, 59.17%) - Best for few-shot examples
3. **EvolutionaryOptimizer** (Rank #3, 52.51%) - Multi-objective optimization
4. **MetaPromptOptimizer** (Rank #4, 38.75%) - LLM critique + MCP tool support
5. **GepaOptimizer** (Rank #5, 32.27%) - Single-turn tasks
6. **ParameterOptimizer** - LLM parameter tuning (temperature, top_p)

**When to use each algorithm:**

See `ALGORITHM_SELECTION_GUIDE` constant in `opik_client.py` or access via:

```python
from deep_agent.integrations import ALGORITHM_SELECTION_GUIDE
print(ALGORITHM_SELECTION_GUIDE)
```

### MCP Clients - Web Search

Perform web searches using Perplexity MCP server:

```python
from deep_agent.integrations.mcp_clients import PerplexityClient

# Initialize client
client = PerplexityClient()

# Perform search
results = await client.search(
    query="machine learning trends 2024",
    max_results=5
)

# Format results for agent consumption
formatted = client.format_results_for_agent(results)
print(formatted)

# Extract source URLs for citations
sources = client.extract_sources(results)
print(f"Sources: {sources}")
```

**Features:**
- Async/await support for high-performance I/O
- Automatic retry logic with exponential backoff
- Rate limiting (10 requests/minute default)
- Query sanitization to prevent injection attacks
- Result formatting for agent consumption
- Citation tracking for provenance

**Configuration:**

MCP server configuration in `.mcp/perplexity.json`:

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "python",
      "args": ["-m", "perplexity_mcp"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "PERPLEXITY_MODEL": "sonar"
      }
    }
  }
}
```

**Environment variables:**
```bash
PERPLEXITY_API_KEY=pplx_xxx...
MCP_PERPLEXITY_TIMEOUT=30  # Optional, defaults to 30s
```

## Dependencies

### Phase 0 (Required)
- `langsmith>=0.4.0` - LangSmith tracing SDK
- `mcp>=1.0.0` - Model Context Protocol library
- `tenacity>=8.0.0` - Retry logic with exponential backoff

### Phase 1 (Optional)
- `opik>=0.4.0` - Opik prompt optimization SDK
- `opik-optimizer>=2.2.1` - 6 optimization algorithms
- `gepa` - GEPA algorithm (auto-installed with opik-optimizer)

### External Services
- `perplexity_mcp` - Perplexity MCP server (installed separately)

**Installation:**

```bash
# Phase 0 dependencies
poetry install

# Phase 1 dependencies (optional)
poetry install --with phase1

# Perplexity MCP server
pip install perplexity-mcp
```

## Related Documentation

- [MCP Clients](mcp_clients/README.md) - Detailed MCP client documentation
- [Services](../services/README.md) - Service layer using integrations
- [LangSmith Python SDK](https://docs.smith.langchain.com/reference/python/reference)
- [Opik Documentation](https://www.comet.com/docs/opik/)
- [MCP Specification](https://modelcontextprotocol.io/)

## Architecture Notes

### Lazy Loading Design

The lazy loading pattern is implemented using Python's `__getattr__` hook:

```python
# integrations/__init__.py
def __getattr__(name):
    if name in ("OpikClient", ...):
        from deep_agent.integrations.opik_client import OpikClient
        globals()["OpikClient"] = OpikClient  # Cache for next access
        return OpikClient
    raise AttributeError(...)
```

**Trade-offs:**
- ✅ Phase 0 works without Phase 1 packages
- ✅ Faster startup (fewer imports)
- ✅ Clear dependency separation
- ⚠️ First access slightly slower (one-time import)
- ⚠️ Less explicit (imports hidden behind __getattr__)

### Singleton Pattern

`get_opik_client()` uses singleton pattern to avoid multiple API client initializations:

```python
_opik_client: Optional[OpikClient] = None

def get_opik_client(settings: Optional[Settings] = None) -> OpikClient:
    global _opik_client
    if _opik_client is None:
        _opik_client = OpikClient(settings=settings)
    return _opik_client
```

**Benefits:**
- Single API connection per process
- Shared configuration across modules
- Reduced API overhead

**Limitations:**
- Not thread-safe (Phase 0 acceptable)
- Global state (add threading.Lock in Phase 1 if needed)

### Error Handling

All integrations follow consistent error handling:

1. **Validation errors** - Raise immediately (ValueError, TypeError)
2. **Network errors** - Retry with exponential backoff (tenacity)
3. **API errors** - Log and raise (RuntimeError with details)
4. **Timeout errors** - Raise TimeoutError with context

Example:

```python
try:
    results = await client.search("query")
except ValueError as e:
    # Invalid input - don't retry
    logger.error("Invalid query", error=str(e))
    raise
except (ConnectionError, TimeoutError) as e:
    # Network issue - already retried
    logger.error("Network failure after retries", error=str(e))
    raise
except RuntimeError as e:
    # API error (rate limit, auth failure)
    logger.error("API error", error=str(e))
    raise
```

## Testing

### Unit Tests
- `tests/unit/test_integrations/test_langsmith.py` - LangSmith setup
- `tests/unit/test_integrations/test_opik_client.py` - Opik client (mocked)
- `tests/unit/test_integrations/test_mcp_clients/test_perplexity.py` - Perplexity client

### Integration Tests
- `tests/integration/test_langsmith_tracing.py` - Real LangSmith traces
- `tests/integration/test_perplexity_search.py` - Real Perplexity searches

### Live API Tests
- `tests/live_api/test_perplexity_integration.py` - Perplexity MCP (Phase 0.5)
- `tests/live_api/test_langsmith_integration.py` - LangSmith tracing (Phase 0.5)

**Running tests:**

```bash
# Unit tests (fast, mocked)
pytest tests/unit/test_integrations/ -v

# Integration tests (slower, real API calls)
pytest tests/integration/test_*_integration.py -v

# Live API tests (costs money, run manually)
./scripts/test_live_api.sh  # Phase 0.5
```

## Security Considerations

### API Key Masking

All API keys are masked in logs using `mask_api_key()` utility:

```python
from deep_agent.core.security import mask_api_key

masked = mask_api_key("lsv2_1234567890abcdef")
logger.info("API key configured", key=masked)  # "lsv2_***...cdef"
```

### Rate Limiting

MCP clients implement rate limiting to prevent API abuse:

```python
# Perplexity default: 10 requests/minute
client = PerplexityClient()

# Raises RuntimeError if exceeded
try:
    await client.search("query")
except RuntimeError as e:
    print(f"Rate limited: {e}")
```

### Input Sanitization

Search queries are sanitized to prevent injection attacks:

```python
# Removes dangerous characters, limits length
def _sanitize_query(self, query: str) -> str:
    sanitized = re.sub(r"[^\w\s\-.,?!']", "", query)
    return sanitized[:MAX_QUERY_LENGTH].strip()
```

### Timeout Enforcement

All network requests enforce timeouts to prevent hanging:

```python
async with asyncio.timeout(self.timeout):
    result = await session.call_tool(...)
```

## Future Enhancements (Phase 2+)

### Custom MCP Servers

Build custom MCP servers using `fastmcp`:

```python
# custom_mcp/research.py
from fastmcp import FastMCP

mcp = FastMCP("Research Server")

@mcp.tool()
async def search_papers(query: str) -> list[dict]:
    """Search academic papers."""
    # Implementation
    return results
```

### Additional Integrations

- **Gmail MCP** - Email analysis and management
- **Calendar MCP** - Calendar integration
- **GitHub MCP** - Repository operations
- **Database MCP** - Database query tools

### Enhanced Opik Features

- Multi-metric optimization (score vs. latency vs. cost)
- Automated A/B testing pipelines
- Prompt variant management
- Real-time optimization feedback

### LangSmith Enhancements

- Custom evaluation datasets
- Automated performance regression detection
- Cost tracking and budgeting
- Team collaboration features
