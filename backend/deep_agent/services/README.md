# Services

## Purpose

The services layer provides the business logic layer that orchestrates agent operations, state management, and coordinates between the API layer and agent implementations.

**Architecture Position:**
```
API Layer (FastAPI endpoints)
    ↓
Services Layer (business logic, orchestration)  ← YOU ARE HERE
    ↓
Agents Layer (LangGraph DeepAgents, tools, integrations)
```

## Key Files

### `agent_service.py`
Main agent orchestration service providing:
- **Lazy Initialization**: Agents created on first use with thread-safe async locks
- **Invocation Methods**: Both streaming (`stream()`) and non-streaming (`invoke()`) support
- **State Management**: Checkpointer-based conversation persistence (`get_state()`, `update_state()`)
- **HITL Support**: Human-in-the-loop approval workflows
- **Retry Logic**: Exponential backoff for transient failures (ConnectionError, TimeoutError, OSError)
- **Observability**: LangSmith trace capture and structured logging
- **Prompt Variants**: A/B testing support for prompt optimization

**Key Methods:**
- `invoke(message, thread_id)` - Non-streaming agent invocation
- `stream(message, thread_id)` - Streaming agent response via astream_events()
- `get_state(thread_id)` - Retrieve conversation state from checkpointer
- `update_state(thread_id, values)` - Update state (HITL approval)

### `llm_factory.py`
Factory functions for creating LangChain-compatible LLM instances:
- **GPT-5 Configuration**: Reasoning effort, max tokens, streaming
- **Type Safety**: Structured configuration via GPT5Config dataclass
- **Validation**: API key format validation
- **Flexibility**: Override config values via kwargs

**Key Functions:**
- `create_gpt5_llm(api_key, config, **kwargs)` - Create ChatOpenAI instance for GPT-5

## Usage

### Basic Agent Invocation (Non-Streaming)

```python
from deep_agent.services.agent_service import AgentService

# Create service instance
service = AgentService()

# Invoke agent
result = await service.invoke(
    message="What files are in the current directory?",
    thread_id="user-123"
)

# Access response
assistant_message = result["messages"][-1]["content"]
trace_id = result.get("trace_id")  # LangSmith trace ID
```

### Streaming Agent Response

```python
from deep_agent.services.agent_service import AgentService

# Create service instance
service = AgentService()

# Stream agent response
async for event in service.stream("Hello", "user-456"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        if hasattr(chunk, "content"):
            print(chunk.content, end="")
```

### State Management (HITL Workflow)

```python
from deep_agent.services.agent_service import AgentService

service = AgentService()

# Get current state
state = await service.get_state("user-123")
print(state["values"]["messages"])
print("Running" if state["next"] else "Completed")

# Update state (approve HITL request)
await service.update_state(
    thread_id="user-123",
    values={"approved": True},
    as_node="human"
)
```

### A/B Testing with Prompt Variants

```python
from deep_agent.services.agent_service import AgentService

# Test with balanced prompt variant
service_balanced = AgentService(prompt_variant="balanced")
result_balanced = await service_balanced.invoke("Hello", "user-123")

# Test with max compression prompt variant
service_compressed = AgentService(prompt_variant="max_compression")
result_compressed = await service_compressed.invoke("Hello", "user-456")

# Compare results (e.g., via Opik evaluation)
```

### Creating Custom LLM Instances

```python
from deep_agent.services.llm_factory import create_gpt5_llm
from deep_agent.models.gpt5 import GPT5Config, ReasoningEffort

# Create LLM with custom config
config = GPT5Config(
    reasoning_effort=ReasoningEffort.HIGH,
    max_tokens=8000
)
llm = create_gpt5_llm(api_key="sk-...", config=config)

# Use with DeepAgents
from deep_agent.agents.deep_agent import create_agent
agent = await create_agent(settings=settings, custom_llm=llm)
```

## Architecture Pattern

The services layer implements several key patterns:

### 1. Lazy Initialization
Agents are expensive to create, so we create them lazily on first use:

```python
async def _ensure_agent(self) -> CompiledStateGraph:
    """Thread-safe lazy agent creation."""
    if self.agent is not None:
        return self.agent  # Fast path

    async with self._agent_lock:  # Prevent race conditions
        if self.agent is not None:
            return self.agent  # Double-check after lock

        self.agent = await create_agent(...)  # Create once
        return self.agent
```

**Benefits:**
- No upfront cost if agent never invoked
- Single instance reused for all invocations
- Thread-safe for concurrent requests

### 2. State Persistence
LangGraph checkpointer provides conversation state persistence:

```python
# Config includes thread_id for state tracking
config = {
    "configurable": {
        "thread_id": thread_id
    }
}

# Agent automatically loads/saves state via checkpointer
result = await agent.ainvoke(input_data, config)
```

**Benefits:**
- Multi-turn conversations work seamlessly
- State survives restarts (MemorySaver stores in-memory, future: PostgreSQL)
- HITL workflows can pause/resume

### 3. Streaming Events
LangGraph's `astream_events()` provides fine-grained event streaming:

```python
async for event in agent.astream_events(input_data, config, version="v2"):
    event_type = event.get("event")

    if event_type == "on_chat_model_stream":
        # LLM token streaming
        chunk = event["data"]["chunk"]
        print(chunk.content, end="")

    elif event_type == "on_tool_start":
        # Tool execution started
        tool_name = event["name"]
        print(f"Tool {tool_name} started")

    elif event_type == "on_tool_end":
        # Tool execution completed
        result = event["data"]["output"]
        print(f"Tool result: {result}")
```

**Benefits:**
- Real-time UI updates
- Progress indicators for long-running operations
- Tool execution visibility

### 4. Retry Logic
Exponential backoff for transient failures:

```python
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

async for attempt in AsyncRetrying(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
):
    with attempt:
        result = await agent.ainvoke(input_data, config)
```

**Benefits:**
- Resilience to network blips
- Automatic recovery from transient errors
- Configurable retry strategy

### 5. Observability
LangSmith integration for tracing:

```python
from langsmith import get_current_run_tree

# Capture trace_id for debugging
run_tree = get_current_run_tree()
if run_tree:
    trace_id = str(run_tree.trace_id)
    logger.info("Agent invoked", trace_id=trace_id)
```

**Benefits:**
- Full execution traces in LangSmith UI
- Performance analysis
- Error debugging with full context

## Dependencies

### Internal Dependencies
- `../agents/deep_agent.py` - Agent creation via `create_agent()`
- `../integrations/langsmith.py` - Tracing configuration
- `../integrations/perplexity.py` - Web search via Perplexity MCP (indirectly via tools)
- `../models/gpt5.py` - GPT-5 configuration dataclasses
- `../config/settings.py` - Application settings via `get_settings()`
- `../core/logging.py` - Structured logging via `get_logger()`

### External Dependencies
- `langchain` - LLM abstractions and chains
- `langgraph` - Agent graph framework (CompiledStateGraph, checkpointer)
- `langsmith` - Tracing and observability (get_current_run_tree)
- `langchain_openai` - OpenAI integration (ChatOpenAI)
- `tenacity` - Retry logic with exponential backoff

## Related Documentation

- [Agents](../agents/README.md) - Agent implementations and tools
- [API](../api/README.md) - FastAPI endpoints that use these services
- [Integrations](../integrations/README.md) - External service integrations (LangSmith, Perplexity)
- [Models](../models/README.md) - Data models and GPT-5 configuration
- [Config](../config/README.md) - Settings and environment management

## Testing

### Unit Tests
```bash
pytest tests/unit/test_services/ -v
```

**Coverage:**
- `test_agent_service.py` - AgentService methods, lazy initialization, retry logic
- `test_llm_factory.py` - LLM factory functions, validation

### Integration Tests
```bash
pytest tests/integration/test_services/ -v
```

**Coverage:**
- `test_agent_service_integration.py` - End-to-end agent invocations with real checkpointer
- `test_streaming_integration.py` - Streaming workflows via astream_events()
- `test_hitl_workflow.py` - HITL state management (get_state, update_state)

### Test Markers
```python
@pytest.mark.unit  # Unit tests (mocked dependencies)
@pytest.mark.integration  # Integration tests (real dependencies)
@pytest.mark.asyncio  # Async test support
```

## Configuration

### Environment Variables

The services layer respects these settings from `config/settings.py`:

```python
# Agent Configuration
ENABLE_HITL=true              # Enable HITL approval workflows
ENABLE_SUB_AGENTS=true        # Enable sub-agent delegation

# Streaming Configuration
STREAM_TIMEOUT_SECONDS=600    # Max streaming duration (10 minutes)
STREAM_VERSION=v2             # LangGraph astream_events() API version
STREAM_ALLOWED_EVENTS=["on_chat_model_stream","on_tool_start","on_tool_end"]

# LangSmith Configuration
LANGCHAIN_TRACING_V2=true     # Enable tracing
LANGCHAIN_API_KEY=lsv2_...    # LangSmith API key
LANGCHAIN_PROJECT=deep-agent-one-dev  # Project name
```

### Prompt Variants (A/B Testing)

Prompt variants are configured in `backend/deep_agent/agents/prompts/`:

```
prompts/
├── default/
│   ├── dev.txt       # Development prompt
│   └── prod.txt      # Production prompt
└── variants/
    ├── control.txt          # Baseline prompt
    ├── max_compression.txt  # Maximum token efficiency
    ├── balanced.txt         # Balance quality/cost
    └── conservative.txt     # Maximum quality
```

**Usage:**
```python
# Use default prompt (based on ENV setting)
service = AgentService()

# Use specific variant for A/B testing
service = AgentService(prompt_variant="balanced")
```

**Evaluation:**
Use Opik for A/B testing and prompt optimization (see `docs/development/prompt-optimization.md`).

## Error Handling

### Common Exceptions

```python
from deep_agent.services.agent_service import AgentService

service = AgentService()

try:
    result = await service.invoke("Hello", "user-123")
except ValueError as e:
    # Invalid input (empty message, invalid thread_id)
    print(f"Invalid input: {e}")
except RuntimeError as e:
    # Agent execution failure
    print(f"Agent failed: {e}")
    # Check LangSmith trace for details
except asyncio.TimeoutError as e:
    # Streaming timeout
    print(f"Streaming timed out after {STREAM_TIMEOUT_SECONDS}s")
except asyncio.CancelledError as e:
    # Client disconnected or task cancelled
    print("Operation cancelled")
```

### Logging

All service operations emit structured logs:

```json
{
  "message": "Agent invocation completed",
  "thread_id": "user-123",
  "trace_id": "00000000-0000-0000-0000-000000000000",
  "message_count": 4,
  "level": "info",
  "timestamp": "2025-11-12T10:30:00.000Z"
}
```

**Log Levels:**
- `DEBUG` - Detailed execution flow (agent creation, state operations)
- `INFO` - Key events (invocation start/end, trace IDs)
- `WARNING` - Retry attempts, API key format issues
- `ERROR` - Failures with trace IDs and LangSmith URLs

## Performance Considerations

### Lazy Initialization
- **First invocation:** ~1-2s (agent creation)
- **Subsequent invocations:** <100ms (reuse agent)

### Streaming vs. Non-Streaming
- **Non-streaming (`invoke()`)**: Wait for complete response, simpler API
- **Streaming (`stream()`)**: Real-time updates, better UX for long responses

### Concurrent Requests
- Thread-safe agent initialization (async lock)
- Single agent instance handles all requests (stateless)
- State persistence via checkpointer (thread_id isolation)

### Retry Strategy
- Max 3 attempts for transient failures
- Exponential backoff: 2s → 4s → 8s (max 10s)
- Only retries: ConnectionError, TimeoutError, OSError
- Does NOT retry: ValueError, RuntimeError (permanent failures)

## Future Enhancements (Phase 1+)

### Memory System Integration
```python
# Phase 1: Semantic memory retrieval
service = AgentService()
result = await service.invoke(
    message="What did we discuss last week?",
    thread_id="user-123",
    enable_memory=True  # Retrieve relevant past conversations
)
```

### PostgreSQL Checkpointer
```python
# Phase 1: Replace MemorySaver with PostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(connection_string="postgresql://...")
service = AgentService(checkpointer=checkpointer)
```

### Reasoning Router
```python
# Phase 1: Dynamic reasoning effort based on query complexity
from deep_agent.services.reasoning_router import ReasoningRouter

router = ReasoningRouter()
effort = router.route(message="Analyze this complex dataset")  # → HIGH
service = AgentService(reasoning_effort=effort)
```

### Custom MCP Servers
```python
# Phase 2: Custom tools via fastmcp
from deep_agent.services.mcp_service import MCPService

mcp = MCPService()
await mcp.register_server("research", "./mcp_servers/research_server.py")
service = AgentService(mcp=mcp)
```

---

**Last Updated:** 2025-11-12
**Phase:** 0 (MVP Complete)
**Next Review:** Phase 1 Start
