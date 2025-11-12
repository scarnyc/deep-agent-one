# Backend

## Purpose

Backend API and agent infrastructure for Deep Agent AGI - a FastAPI-based service that orchestrates LangGraph DeepAgents with GPT-5, providing real-time agent interactions, tool execution, and human-in-the-loop workflows.

---

## Directory Structure

```
backend/
└── deep_agent/             # Core Deep Agent AGI implementation
    ├── agents/             # LangGraph agent implementations
    ├── api/                # FastAPI routes and endpoints
    ├── config/             # Configuration management
    ├── core/               # Core utilities (logging, errors, security)
    ├── integrations/       # External service integrations
    ├── models/             # Data models and LLM configuration
    ├── services/           # Business logic layer
    ├── tools/              # Agent tools (web search, prompt optimization)
    └── main.py             # FastAPI application entry point
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Poetry (dependency management)
- OpenAI API key (GPT-5)
- Node.js 18+ (for frontend development)

### Installation

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
cd backend
poetry install

# 3. Set up environment variables
cp ../.env.example ../.env
# Edit .env with your API keys

# 4. Start backend server
cd ..
./scripts/start-backend.sh
```

### Development Server

```bash
# Start with auto-reload (development)
./scripts/start-backend.sh

# Backend runs at: http://127.0.0.1:8000
# API docs at: http://127.0.0.1:8000/docs
# Health check: http://127.0.0.1:8000/health
```

---

## Technology Stack

### Core Framework
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server with auto-reload
- **Pydantic** - Data validation and settings
- **Python 3.10+** - Modern Python with type hints

### Agent Framework
- **LangGraph** - Agent state management and orchestration
- **LangChain** - LLM integration and tool chaining
- **DeepAgents** - Advanced planning and delegation capabilities

### LLM Integration
- **OpenAI GPT-5** - Primary LLM with variable reasoning effort
- **LangSmith** - Agent tracing and observability
- **Perplexity MCP** - Web search via Model Context Protocol

### State Management
- **SQLite** - Agent checkpointer (development)
- **PostgreSQL + pgvector** - Planned for Phase 1 (production)

### Real-Time Communication
- **WebSockets** - Bidirectional agent-client communication
- **AG-UI Protocol** - Event streaming for agent transparency
- **Server-Sent Events** - Alternative streaming (planned)

---

## Core Modules

### [`deep_agent/`](deep_agent/README.md)
Core Deep Agent AGI implementation with agents, API, services, and integrations.

**Key Components:**
- Agent orchestration and lifecycle management
- FastAPI endpoints (REST + WebSocket)
- Business logic and state management
- External service integrations (LangSmith, Perplexity)

### [`deep_agent/agents/`](deep_agent/agents/README.md)
LangGraph agent implementations with planning, delegation, and HITL workflows.

**Features:**
- DeepAgent initialization and configuration
- System prompts with context engineering
- Checkpointing for conversation persistence
- Reasoning router for variable effort (GPT-5)

### [`deep_agent/api/`](deep_agent/api/README.md)
FastAPI routes, WebSocket endpoints, and middleware.

**Endpoints:**
- `POST /api/v1/chat` - Streaming chat completions
- `WS /api/v1/ws` - WebSocket agent interactions
- `POST /api/v1/agents/invoke` - Agent invocations
- `GET /health` - Health check

### [`deep_agent/services/`](deep_agent/services/README.md)
Business logic layer orchestrating agent operations.

**Services:**
- `AgentService` - Main orchestration service
- `LLM Factory` - LangChain-compatible LLM creation
- State management and retry logic

### [`deep_agent/integrations/`](deep_agent/integrations/README.md)
External service integrations (LangSmith, Perplexity, Opik).

**Integrations:**
- LangSmith tracing and observability
- Perplexity web search via MCP
- Opik prompt optimization (Phase 1)

### [`deep_agent/tools/`](deep_agent/tools/README.md)
Agent tools for web search, prompt optimization, and file operations.

**Tools:**
- `web_search` - Perplexity-powered web search
- `prompt_optimization` - A/B testing and optimization (Phase 1)
- DeepAgent built-in tools (ls, read_file, write_file, edit_file)

### [`deep_agent/models/`](deep_agent/models/README.md)
Data models and GPT-5 configuration.

**Models:**
- Chat request/response models
- Agent configuration models
- GPT-5 reasoning effort configuration

### [`deep_agent/config/`](deep_agent/config/README.md)
Application configuration and settings management.

**Configuration:**
- Environment-specific settings (.env)
- API keys and secrets
- Model configuration (GPT-5 parameters)

### [`deep_agent/core/`](deep_agent/core/README.md)
Core utilities for logging, error handling, and security.

**Utilities:**
- Structured logging with context
- Custom error classes
- Security helpers (input sanitization, rate limiting)

---

## API Documentation

### REST API

Full API documentation available at:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### WebSocket API

**Endpoint**: `ws://127.0.0.1:8000/api/v1/ws`

**Message Format** (AG-UI Protocol):
```json
{
  "type": "user_message",
  "threadId": "user-123",
  "content": "What files are in the current directory?"
}
```

**Response Events**:
- `on_chain_start` - Agent chain started
- `on_chat_model_stream` - Token streaming
- `on_tool_start` - Tool execution started
- `on_tool_end` - Tool execution completed
- `on_chain_end` - Agent chain completed

See [API README](deep_agent/api/README.md) for detailed event schemas.

---

## Development Workflow

### Running Tests

```bash
# All tests
pytest

# Backend tests only
pytest tests/unit/ tests/integration/

# With coverage
pytest --cov=deep_agent --cov-report=html
```

### Code Quality

```bash
# Linting and formatting
ruff check backend/
ruff format backend/

# Type checking
mypy backend/deep_agent/

# Security scanning
./scripts/security_scan.sh
```

### Pre-Commit Workflow

Per CLAUDE.md, run these agents before EVERY commit:

```bash
# 1. testing-expert (if tests written)
# Use Task tool with testing-expert subagent

# 2. code-review-expert (for all code)
# Use Task tool with code-review-expert subagent
# - Runs TheAuditor security scan automatically
# - Verifies type hints, error handling, testing
# - Provides commit approval status

# 3. Only after approval: Commit
git add backend/
git commit -m "feat(backend): description"
```

### Adding New Endpoints

1. **Define route** in `deep_agent/api/v1/`
2. **Add request/response models** in `deep_agent/models/`
3. **Implement business logic** in `deep_agent/services/`
4. **Write tests** (unit + integration)
5. **Update API documentation** in docstrings
6. **Run pre-commit review** (testing-expert + code-review-expert)
7. **Commit** with semantic message

---

## Architecture Patterns

### Three-Tier Architecture

```
API Layer (FastAPI endpoints)
    |
    v
Services Layer (business logic, orchestration)
    |
    v
Agents Layer (LangGraph DeepAgents, tools, integrations)
```

### Key Design Patterns

- **Lazy Initialization**: Agents created on first use for performance
- **State Management**: LangGraph checkpointer for conversation persistence
- **Streaming Support**: AsyncGenerator for real-time responses via `astream_events()`
- **Retry Logic**: Exponential backoff for transient failures
- **Thread Safety**: Async locks for concurrent agent creation

### Error Handling

```python
from deep_agent.core.errors import AgentError, ToolError

try:
    result = await agent_service.invoke(message, thread_id)
except AgentError as e:
    logger.error(f"Agent error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Logging

```python
from deep_agent.core.logging import get_logger

logger = get_logger(__name__)
logger.info("Agent invoked", extra={"thread_id": thread_id, "message_length": len(message)})
```

---

## Configuration

### Environment Variables

Required in `.env`:

```bash
# OpenAI API
OPENAI_API_KEY=sk-...

# LangSmith (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=deep-agent-agi

# Server
HOST=127.0.0.1
PORT=8000

# Database (Phase 1)
DATABASE_URL=postgresql://user:pass@localhost:5432/deep_agent
```

### Model Configuration

Edit `deep_agent/models/gpt5.py`:

```python
GPT5_CONFIG = {
    "model": "gpt-5-preview",
    "temperature": 0.7,
    "max_tokens": 4096,
    "reasoning_effort": "medium",  # low, medium, high
}
```

---

## Performance

### Expected Metrics (Phase 0)

- **Response Latency**: <2s for simple queries
- **Token Streaming**: <500ms time to first token
- **WebSocket Reconnect**: <1s
- **Agent Initialization**: <300ms (cached)

### Optimization Tips

1. **Use streaming**: `astream_events()` for real-time responses
2. **Cache agents**: Lazy initialization with singleton pattern
3. **Batch requests**: Group multiple invocations when possible
4. **Monitor traces**: Use LangSmith for performance insights

---

## Security

### Best Practices

- **API Key Storage**: Never commit `.env` to version control
- **Input Validation**: Pydantic models validate all input
- **Rate Limiting**: `slowapi` middleware on all endpoints
- **Prompt Injection**: Sanitize user input before passing to LLM
- **Error Messages**: Don't expose internal details in API responses

### TheAuditor Integration

Run security scans before every commit:

```bash
./scripts/security_scan.sh

# Review findings
cat .pf/readthis/*
```

---

## Monitoring & Observability

### LangSmith Tracing

All agent operations are traced automatically:

**View traces**: https://smith.langchain.com/

**Example trace data**:
- Agent invocation inputs/outputs
- Tool calls with arguments and results
- Token usage and costs
- Execution time breakdown

### Logging

Structured logs written to:
- **Console**: Development (colorized)
- **File**: `logs/backend/YYYY-MM-DD-HH-MM-SS.log`

**Log Levels**:
- `DEBUG`: Detailed debugging info
- `INFO`: General operations
- `WARNING`: Recoverable errors
- `ERROR`: Critical failures

### Health Checks

```bash
# Check backend health
curl http://127.0.0.1:8000/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:30:00Z",
  "version": "0.1.0-phase0"
}
```

---

## Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'deep_agent'`

```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Reinstall dependencies
poetry install
```

#### Issue: Backend won't start - port already in use

```bash
# Solution: Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn deep_agent.main:app --port 8001
```

#### Issue: OpenAI API key not found

```bash
# Solution: Set up .env file
cp .env.example .env
vim .env  # Add OPENAI_API_KEY=sk-...

# Verify environment variables loaded
source .env
echo $OPENAI_API_KEY
```

#### Issue: Agent hangs during startup

**Symptoms**: Uvicorn worker never prints "Started server process"

**Causes**:
- Missing dependencies (opik, opik-optimizer)
- Module-level imports of uninstalled packages
- Encoding issues in Python files

**Solutions**:
```bash
# 1. Install missing dependencies
pip install opik opik-optimizer

# 2. Check for encoding issues
file backend/deep_agent/**/*.py | grep -v "UTF-8\|ASCII"

# 3. Review recent commits for breaking changes
git log --oneline -10
```

#### Issue: WebSocket connection fails

```bash
# Check backend is running
curl http://127.0.0.1:8000/health

# Test WebSocket endpoint
python scripts/test_websocket_streaming.py

# Check backend logs
tail -f logs/backend/*.log
```

---

## Related Documentation

- **[Root README](../README.md)** - Project overview and architecture
- **[CLAUDE.md](../CLAUDE.md)** - Development guide and workflow
- **[Scripts](../scripts/README.md)** - Development and deployment scripts
- **[Tests](../tests/README.md)** - Testing strategy and guidelines
- **[Frontend](../frontend/README.md)** - Next.js frontend documentation

---

## Contributing

### Contribution Workflow

1. **Create feature branch**: `git checkout -b feat/your-feature`
2. **Write tests first** (TDD): Unit + integration tests
3. **Implement feature**: Follow architecture patterns
4. **Run quality checks**: Ruff, mypy, pydocstyle
5. **Run pre-commit agents**: testing-expert + code-review-expert
6. **Commit with semantic message**: `feat(module): description`
7. **Create pull request**: Link to related issues

### Coding Standards

- **Type Hints**: All functions/methods must have type hints
- **Docstrings**: Google-style docstrings on all modules/classes/functions
- **Error Handling**: Explicit error handling with custom exceptions
- **Logging**: Structured logging with context (thread_id, user_id, etc.)
- **Testing**: 80%+ coverage for all new code

### Review Checklist

Before requesting review:

- [ ] Tests pass locally (`pytest`)
- [ ] Coverage ≥80% (`pytest --cov`)
- [ ] Type checking passes (`mypy backend/`)
- [ ] Linting passes (`ruff check backend/`)
- [ ] Security scan passes (`./scripts/security_scan.sh`)
- [ ] testing-expert approval received
- [ ] code-review-expert approval received
- [ ] Documentation updated (docstrings + README)

---

## Roadmap

### Phase 0 (Current - MVP)
- [x] FastAPI backend with WebSocket support
- [x] LangGraph DeepAgents integration
- [x] GPT-5 integration with streaming
- [x] LangSmith tracing
- [x] Perplexity web search
- [ ] Complete E2E test coverage

### Phase 1 (Next - Productionization)
- [ ] Variable reasoning effort (GPT-5 optimization)
- [ ] Memory system (PostgreSQL + pgvector)
- [ ] Authentication & IAM (OAuth 2.0)
- [ ] Provenance store (source tracking)
- [ ] Prompt optimization (Opik integration)

### Phase 2 (Future - Deep Research)
- [ ] Deep research framework (LangChain)
- [ ] Custom MCP servers (fastmcp)
- [ ] Infrastructure hardening (Cloudflare WAF)
- [ ] Load balancing and scaling

---

**Last Updated**: 2025-11-12
**Maintained By**: Deep Agent AGI Team
