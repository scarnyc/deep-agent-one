# Deep Agent AGI - Core Module

## Purpose

Core implementation of Deep Agent AGI - a LangGraph-based agent framework with GPT-5 integration, providing intelligent agent orchestration, tool execution, streaming responses, and human-in-the-loop workflows.

This module implements the complete agent lifecycle from API requests through business logic to LLM interactions, with comprehensive observability and state management.

---

## Architecture Overview

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ API Layer (FastAPI)                                         │
│ - REST endpoints (POST /chat, POST /agents/invoke)          │
│ - WebSocket endpoint (WS /ws)                                │
│ - Request validation and error handling                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────────────┐
│ Services Layer (Business Logic)                             │
│ - AgentService: Orchestration and lifecycle management      │
│ - LLM Factory: Model creation and configuration             │
│ - State management and retry logic                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       v
┌─────────────────────────────────────────────────────────────┐
│ Agents Layer (LangGraph DeepAgents)                         │
│ - Agent initialization and configuration                     │
│ - Tool execution (web search, file ops, prompt optimization) │
│ - External integrations (LangSmith, Perplexity, Opik)       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Request
    │
    ├─ REST API (POST /chat)
    │   └─ Streaming response (AG-UI events)
    │
    ├─ WebSocket (WS /ws)
    │   └─ Bidirectional event stream
    │
    └─ HTTP API (POST /agents/invoke)
        └─ JSON response

                ↓

AgentService.invoke() or .stream()
    │
    ├─ Load/create agent (lazy initialization)
    ├─ Get LLM from factory (GPT-5 with config)
    ├─ Load conversation state (checkpointer)
    └─ Invoke agent.invoke() or .astream_events()

                ↓

DeepAgent Execution
    │
    ├─ Planning: Break down task into subtasks
    ├─ Tool Selection: Choose appropriate tools
    ├─ Execution: Run tools with retry logic
    ├─ HITL: Request approval if needed
    └─ Synthesis: Generate final response

                ↓

Response Stream
    │
    ├─ AG-UI Events: Token streaming, tool calls, progress
    ├─ LangSmith Traces: Full execution trace
    └─ State Persistence: Checkpointer saves conversation
```

---

## Directory Structure

```
deep_agent/
├── agents/                 # LangGraph agent implementations
│   ├── deep_agent.py           # Main DeepAgent initialization
│   ├── checkpointer.py         # SQLite/PostgreSQL state persistence
│   ├── prompts.py              # System prompts with context engineering
│   ├── prompts_variants.py     # A/B testing variants (Phase 1)
│   ├── reasoning_router.py     # GPT-5 effort optimization (Phase 1)
│   └── sub_agents/             # Specialized sub-agents
│
├── api/                    # FastAPI routes and endpoints
│   ├── v1/                     # API version 1
│   │   ├── chat.py                 # Chat endpoints (REST + WS)
│   │   └── agents.py               # Agent management endpoints
│   ├── middleware.py           # Rate limiting, CORS, error handling
│   └── dependencies.py         # Dependency injection
│
├── config/                 # Configuration management
│   └── settings.py             # Environment settings (Pydantic)
│
├── core/                   # Core utilities
│   ├── logging.py              # Structured logging
│   ├── errors.py               # Custom exceptions
│   ├── security.py             # Input sanitization, rate limiting
│   └── serialization.py        # JSON serialization helpers
│
├── integrations/           # External service integrations
│   ├── langsmith.py            # LangSmith tracing
│   ├── opik_client.py          # Opik prompt optimization (Phase 1)
│   └── mcp_clients/            # Model Context Protocol clients
│       └── perplexity.py           # Perplexity web search MCP
│
├── models/                 # Data models
│   ├── chat.py                 # Chat request/response models
│   ├── agents.py               # Agent configuration models
│   └── gpt5.py                 # GPT-5 configuration and reasoning
│
├── services/               # Business logic layer
│   ├── agent_service.py        # Main orchestration service
│   └── llm_factory.py          # LLM creation and configuration
│
├── tools/                  # Agent tools
│   ├── web_search.py           # Perplexity-powered web search
│   ├── prompt_optimization.py  # A/B testing tools (Phase 1)
│   └── __init__.py             # Tool registration
│
├── main.py                 # FastAPI application entry point
└── __init__.py             # Package initialization
```

---

## Key Modules

### 1. [Agents](agents/README.md) - LangGraph DeepAgents

**Purpose**: Agent lifecycle management, planning, delegation, and HITL workflows.

**Key Files**:
- `deep_agent.py` - Main agent initialization with LangGraph
- `checkpointer.py` - State persistence (SQLite/PostgreSQL)
- `prompts.py` - System prompts engineered for task planning
- `reasoning_router.py` - Variable reasoning effort (Phase 1)

**Usage**:
```python
from deep_agent.agents import create_agent

agent = create_agent()
result = await agent.invoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    config={"configurable": {"thread_id": "user-123"}}
)
```

---

### 2. [API](api/README.md) - FastAPI Endpoints

**Purpose**: REST and WebSocket endpoints for agent interactions.

**Key Endpoints**:
- `POST /api/v1/chat` - Streaming chat completions
- `WS /api/v1/ws` - WebSocket agent interactions
- `POST /api/v1/agents/invoke` - Agent invocations
- `GET /health` - Health check

**Usage**:
```bash
# Streaming chat
curl -X POST http://127.0.0.1:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What files are in the current directory?", "thread_id": "user-123"}'

# WebSocket
wscat -c ws://127.0.0.1:8000/api/v1/ws
```

---

### 3. [Services](services/README.md) - Business Logic

**Purpose**: Orchestration layer between API and agents.

**Key Services**:
- `AgentService` - Main orchestration service
  - `invoke()` - Non-streaming agent invocation
  - `stream()` - Streaming agent responses
  - Agent caching and lazy initialization
- `LLM Factory` - LangChain-compatible LLM creation
  - `create_gpt5_llm()` - GPT-5 with reasoning configuration
  - Model configuration and parameter validation

**Usage**:
```python
from deep_agent.services import AgentService

service = AgentService()

# Non-streaming
result = await service.invoke("Hello", thread_id="user-123")

# Streaming
async for event in service.stream("Hello", thread_id="user-123"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="")
```

---

### 4. [Integrations](integrations/README.md) - External Services

**Purpose**: Integrate with LangSmith, Perplexity, and Opik.

**Key Integrations**:
- **LangSmith** - Agent tracing and observability
- **Perplexity MCP** - Web search via Model Context Protocol
- **Opik** - Prompt optimization and A/B testing (Phase 1)

**Usage**:
```python
from deep_agent.integrations import setup_langsmith

# Enable LangSmith tracing
setup_langsmith()

# All agent operations now automatically traced
```

---

### 5. [Tools](tools/README.md) - Agent Tools

**Purpose**: Implement tools for web search, file operations, and prompt optimization.

**Available Tools**:
- `web_search` - Perplexity-powered web search
- `prompt_optimization` - A/B testing and optimization (Phase 1)
- Built-in DeepAgent tools (ls, read_file, write_file, edit_file)

**Usage**:
```python
from deep_agent.tools import web_search

results = await web_search.invoke({"query": "latest AI news"})
print(results["answer"])
```

---

### 6. [Models](models/README.md) - Data Models

**Purpose**: Pydantic models for validation and serialization.

**Key Models**:
- `ChatRequest` / `ChatResponse` - Chat endpoint models
- `AgentConfig` - Agent configuration
- `GPT5Config` - GPT-5 reasoning effort configuration

**Usage**:
```python
from deep_agent.models.chat import ChatRequest

request = ChatRequest(
    message="What files are in the current directory?",
    thread_id="user-123",
    stream=True
)
```

---

### 7. [Config](config/README.md) - Configuration

**Purpose**: Environment-specific settings and API key management.

**Key Files**:
- `settings.py` - Pydantic settings with .env loading

**Usage**:
```python
from deep_agent.config import get_settings

settings = get_settings()
print(settings.OPENAI_API_KEY)
print(settings.LANGCHAIN_PROJECT)
```

---

### 8. [Core](core/README.md) - Core Utilities

**Purpose**: Shared utilities for logging, errors, and security.

**Key Utilities**:
- **Logging**: Structured logging with context
- **Errors**: Custom exception classes
- **Security**: Input sanitization, rate limiting

**Usage**:
```python
from deep_agent.core.logging import get_logger
from deep_agent.core.errors import AgentError

logger = get_logger(__name__)
logger.info("Agent invoked", extra={"thread_id": "user-123"})

try:
    result = await agent.invoke(message)
except AgentError as e:
    logger.error(f"Agent failed: {e}")
```

---

## Usage Examples

### Example 1: Basic Agent Invocation

```python
from deep_agent.services import AgentService

# Create service
service = AgentService()

# Invoke agent (non-streaming)
result = await service.invoke(
    message="What files are in the current directory?",
    thread_id="user-123"
)

print(result["messages"][-1]["content"])
```

### Example 2: Streaming Agent Response

```python
from deep_agent.services import AgentService

# Create service
service = AgentService()

# Stream agent response
async for event in service.stream("Tell me a joke", thread_id="user-456"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        if hasattr(chunk, "content"):
            print(chunk.content, end="")
```

### Example 3: Agent with Web Search Tool

```python
from deep_agent.services import AgentService

# Create service
service = AgentService()

# Agent will automatically use web_search tool when needed
result = await service.invoke(
    message="What's the latest news about AI?",
    thread_id="user-789"
)

# Check tool usage in result
for message in result["messages"]:
    if "tool_calls" in message:
        print(f"Tool called: {message['tool_calls']}")
```

### Example 4: Multi-Turn Conversation

```python
from deep_agent.services import AgentService

# Create service
service = AgentService()

# Same thread_id maintains conversation context
thread_id = "user-123"

# Turn 1
result1 = await service.invoke("My name is Alice", thread_id=thread_id)

# Turn 2 (agent remembers previous context)
result2 = await service.invoke("What's my name?", thread_id=thread_id)
print(result2["messages"][-1]["content"])  # "Your name is Alice"
```

### Example 5: HITL Approval Workflow

```python
from deep_agent.services import AgentService

# Create service
service = AgentService()

# Agent will request approval for sensitive operations
async for event in service.stream(
    "Delete all files in /tmp",
    thread_id="user-hitl-001"
):
    if event["event"] == "on_hitl_request":
        print(f"Approval needed: {event['data']['message']}")
        # User responds with approval/rejection
```

---

## Dependencies

### Core Dependencies

- **FastAPI** - Web framework (^0.104.0)
- **LangGraph** - Agent state management (^1.0.1)
- **LangChain** - LLM integration (^1.0.2)
- **OpenAI** - GPT-5 API client (^1.56.0)
- **Pydantic** - Data validation (^2.0.0)
- **Uvicorn** - ASGI server (^0.24.0)

### Integration Dependencies

- **LangSmith** - Tracing (^0.4.38)
- **Perplexity** - Web search (via MCP)
- **Opik** - Prompt optimization (^0.2.0, Phase 1)

### Development Dependencies

- **pytest** - Testing framework (^7.4.0)
- **ruff** - Linting and formatting (^0.1.0)
- **mypy** - Type checking (^1.7.0)
- **pydocstyle** - Docstring validation (^6.3.0)

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...  # Optional

# LangSmith (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=deep-agent-agi

# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=true  # Development only

# Database (Phase 1)
DATABASE_URL=postgresql://user:pass@localhost:5432/deep_agent

# Security
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
```

### Model Configuration

Edit `models/gpt5.py`:

```python
GPT5_CONFIG = {
    "model": "gpt-5-preview",
    "temperature": 0.7,
    "max_tokens": 4096,
    "reasoning_effort": "medium",  # low, medium, high
}
```

---

## Testing

### Run Tests

```bash
# All deep_agent tests
pytest tests/ -k deep_agent

# Unit tests
pytest tests/unit/test_agents/ -v
pytest tests/unit/test_services/ -v
pytest tests/unit/test_tools/ -v

# Integration tests
pytest tests/integration/test_agents/ -v
pytest tests/integration/test_api/ -v

# With coverage
pytest --cov=deep_agent --cov-report=html
```

### Test Coverage Requirements

- **Overall**: ≥80% coverage
- **Critical modules** (agents, services, API): ≥90% coverage
- **New code**: 100% coverage required

---

## Monitoring & Observability

### LangSmith Tracing

All agent operations are automatically traced:

**View traces**: https://smith.langchain.com/

**Trace includes**:
- Agent invocation inputs/outputs
- Tool calls with arguments and results
- Token usage and costs
- Execution time breakdown
- Error stack traces

### Structured Logging

Logs include contextual information:

```python
logger.info(
    "Agent invoked",
    extra={
        "thread_id": thread_id,
        "message_length": len(message),
        "user_id": user_id,
        "tool_count": len(tool_calls)
    }
)
```

**Log files**: `logs/backend/YYYY-MM-DD-HH-MM-SS.log`

### Health Checks

```bash
curl http://127.0.0.1:8000/health

# Response
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:30:00Z",
  "version": "0.1.0-phase0",
  "dependencies": {
    "langsmith": "connected",
    "database": "ready"
  }
}
```

---

## Security

### Best Practices

1. **API Keys**: Never commit `.env` to version control
2. **Input Validation**: All inputs validated with Pydantic models
3. **Rate Limiting**: Applied to all public endpoints
4. **Prompt Injection**: User input sanitized before LLM calls
5. **Error Handling**: Internal details not exposed in API responses

### TheAuditor Integration

Run security scans before every commit:

```bash
./scripts/security_scan.sh

# Review findings
cat .pf/readthis/*
```

---

## Performance

### Expected Metrics (Phase 0)

- **Agent Initialization**: <300ms (cached)
- **Time to First Token**: <500ms
- **Streaming Latency**: <100ms per token
- **Tool Execution**: <2s per tool call
- **WebSocket Reconnect**: <1s

### Optimization Tips

1. **Use streaming**: `astream_events()` for real-time responses
2. **Cache agents**: Lazy initialization with singleton pattern
3. **Batch requests**: Group multiple invocations when possible
4. **Monitor traces**: Use LangSmith for bottleneck identification
5. **Optimize prompts**: Shorter prompts = faster responses + lower costs

---

## Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'deep_agent'`

```bash
# Ensure virtual environment activated
source ../venv/bin/activate

# Reinstall dependencies
poetry install
```

#### Issue: Agent hangs during startup

**Symptoms**: Uvicorn worker never completes initialization

**Causes**:
- Missing dependencies (opik, opik-optimizer)
- Encoding issues in Python files
- Module-level imports of uninstalled packages

**Solutions**:
```bash
# Install missing dependencies
pip install opik opik-optimizer

# Check for encoding issues
file deep_agent/**/*.py | grep -v "UTF-8\|ASCII"

# Review import chain
python -c "import deep_agent.integrations"
```

#### Issue: OpenAI API rate limit errors

```python
# Solution: Implement exponential backoff (already in agent_service.py)
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
async def invoke_with_retry():
    return await agent.invoke(message)
```

#### Issue: WebSocket disconnect during long tool execution

**Cause**: Tool execution time exceeds WebSocket timeout

**Solutions**:
1. Implement progress events (emit status every 5-10 seconds)
2. Increase WebSocket timeout in frontend
3. Use HTTP polling instead of WebSocket for long operations

---

## Related Documentation

- **[Backend Root](../README.md)** - Backend overview and quick start
- **[Project Root](../../README.md)** - Project architecture and roadmap
- **[CLAUDE.md](../../CLAUDE.md)** - Development guide and workflow
- **[Tests](../../tests/README.md)** - Testing strategy and guidelines

---

## Contributing

### Development Workflow

1. **Create feature branch**: `git checkout -b feat/your-feature`
2. **Write tests first** (TDD): Unit + integration tests
3. **Implement feature**: Follow architecture patterns
4. **Run quality checks**: Ruff, mypy, pydocstyle
5. **Run pre-commit agents**: testing-expert + code-review-expert
6. **Commit with semantic message**: `feat(module): description`

### Code Standards

- **Type Hints**: All functions/methods must have type hints
- **Docstrings**: Google-style docstrings on modules/classes/functions
- **Error Handling**: Explicit error handling with custom exceptions
- **Logging**: Structured logging with context
- **Testing**: 80%+ coverage for all new code

### Pre-Commit Checklist

- [ ] Tests pass (`pytest`)
- [ ] Coverage ≥80% (`pytest --cov`)
- [ ] Type checking passes (`mypy deep_agent/`)
- [ ] Linting passes (`ruff check deep_agent/`)
- [ ] Security scan passes (`./scripts/security_scan.sh`)
- [ ] testing-expert approval received
- [ ] code-review-expert approval received
- [ ] Documentation updated

---

## Roadmap

### Phase 0 (Current - MVP)
- [x] DeepAgent initialization and configuration
- [x] FastAPI endpoints (REST + WebSocket)
- [x] GPT-5 integration with streaming
- [x] LangSmith tracing
- [x] Perplexity web search
- [x] Agent service orchestration
- [ ] Complete UI tests (Playwright)

### Phase 1 (Next - Productionization)
- [ ] Variable reasoning effort (reasoning_router.py)
- [ ] Prompt optimization (Opik integration)
- [ ] A/B testing (prompts_variants.py)
- [ ] Memory system (PostgreSQL + pgvector)
- [ ] Authentication & IAM
- [ ] Provenance store

### Phase 2 (Future - Deep Research)
- [ ] Deep research framework
- [ ] Custom MCP servers (fastmcp)
- [ ] Advanced reasoning workflows
- [ ] Multi-agent collaboration

---

**Last Updated**: 2025-11-12
**Maintained By**: Deep Agent AGI Team
