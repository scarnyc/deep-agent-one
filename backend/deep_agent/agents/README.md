# Agents

## Purpose

The agents module is the core orchestration layer of the Deep Agent AGI system, responsible for creating and managing AI agents powered by LangGraph's DeepAgents framework and OpenAI's GPT-5 model. It provides a complete implementation of agent lifecycle management, state persistence, reasoning optimization, and prompt engineering capabilities.

This module abstracts the complexity of agent creation, allowing the rest of the system to easily instantiate fully-configured agents with checkpointing, observability (LangSmith), custom tools (web search), and environment-specific behavior. It serves as the bridge between low-level LLM interactions (services layer) and high-level API endpoints (FastAPI backend).

## Key Files

### Core Agent Files

- **`deep_agent.py`** - Main DeepAgent implementation using LangChain's `create_deep_agent()` API
  - Creates and configures DeepAgents with LLM, tools, checkpointer, and system prompts
  - Integrates GPT-5 via LLM factory with reasoning effort and verbosity control
  - Attaches AsyncSqliteSaver checkpointer for state persistence
  - Supports A/B testing with prompt variants via `prompt_variant` parameter
  - Includes built-in file system tools (ls, read_file, write_file, edit_file, write_todos)
  - Adds custom web_search tool (Perplexity MCP)
  - Configures LangSmith tracing for observability

- **`checkpointer.py`** - State persistence management with LangGraph checkpointers
  - Manages AsyncSqliteSaver (Phase 0) and PostgresSaver (Phase 1+) checkpointers
  - Handles database creation, schema setup, and connection lifecycle
  - Provides cleanup utilities for old checkpoints (configurable retention period)
  - Supports async context manager pattern for resource cleanup
  - Thread-safe state persistence across agent invocations

- **`reasoning_router.py`** - Routing logic for determining optimal GPT-5 reasoning effort
  - Phase 0: Returns MEDIUM for all queries (baseline implementation)
  - Phase 1: Will implement trigger phrase detection and complexity analysis
  - Optimizes cost/performance trade-off by selecting appropriate reasoning levels
  - Placeholder methods for future enhancements (_analyze_trigger_phrases, _calculate_complexity)

### Prompt Engineering Files

- **`prompts.py`** - Environment-specific system prompts with semantic versioning
  - Base system prompt (DEEP_AGENT_SYSTEM_PROMPT) with core capabilities and guidelines
  - Development-specific appendix (DEEP_AGENT_INSTRUCTIONS_DEV) with verbose reasoning
  - Production-specific appendix (DEEP_AGENT_INSTRUCTIONS_PROD) with efficiency focus
  - Environment-aware prompt selection via `get_agent_instructions()`
  - Prompt version tracking (current: v1.1.0) for monitoring prompt evolution
  - Includes web search citation guidelines, parallel tool execution limits, accuracy/verbosity balance

- **`prompts_variants.py`** - A/B testing variants for prompt optimization experiments
  - Four prompt variants: control (baseline), max_compression (50% reduction), balanced (35% reduction), conservative (20% reduction)
  - Deterministic variant selection via user_id hashing for consistent A/B testing
  - Metadata tracking (token estimates, reduction targets, focus areas)
  - Random variant selection for anonymous users
  - Integrates with Opik for automated prompt optimization workflows

### Sub-Agent Directory

- **`sub_agents/`** - Specialized sub-agent implementations (Phase 1+)
  - Placeholder structure for future specialized agents (research, code review, testing)
  - Sub-agent prompts stored in `sub_agents/prompts/`
  - DeepAgents supports sub-agent delegation via `delegate_to_subagent` tool

## Usage

### Basic Agent Creation

```python
from deep_agent.agents.deep_agent import create_agent

# Create agent with default settings
agent = await create_agent()

# Invoke agent with a simple query
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "Hello, how are you?"}]},
    {"configurable": {"thread_id": "user-123"}}
)

# Access response
print(result["messages"][-1]["content"])
```

### Agent with Checkpointer (State Persistence)

```python
from deep_agent.agents.deep_agent import create_agent
from deep_agent.agents.checkpointer import CheckpointerManager

# Create checkpointer and agent
async with CheckpointerManager() as manager:
    checkpointer = await manager.create_checkpointer()
    agent = await create_agent()  # checkpointer auto-attached via settings

    # Multi-turn conversation with state persistence
    config = {"configurable": {"thread_id": "user-123"}}

    # First turn
    result1 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "My name is Alice"}]},
        config
    )

    # Second turn (agent remembers previous context)
    result2 = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "What's my name?"}]},
        config
    )
    print(result2["messages"][-1]["content"])  # "Your name is Alice"
```

### A/B Testing with Prompt Variants

```python
from deep_agent.agents.deep_agent import create_agent
from deep_agent.agents.prompts_variants import get_variant_metadata

# Test with balanced variant (35% token reduction)
agent_balanced = await create_agent(prompt_variant="balanced")

# Test with max_compression variant (50% token reduction)
agent_compressed = await create_agent(prompt_variant="max_compression")

# Get metadata for comparison
metadata = get_variant_metadata("balanced")
print(f"Using variant: {metadata['description']}")
print(f"Estimated tokens: {metadata['estimated_tokens']}")
print(f"Focus: {metadata['focus']}")
```

### Deterministic Variant Selection (User-Based)

```python
from deep_agent.agents.prompts_variants import select_prompt_variant

# Same user always gets same variant
user_id = "user-123"
variant_name, prompt_text = select_prompt_variant(user_id=user_id)
print(f"User {user_id} assigned to variant: {variant_name}")

# Create agent with selected variant
agent = await create_agent(prompt_variant=variant_name)
```

### Checkpointer Cleanup (Maintenance)

```python
from deep_agent.agents.checkpointer import CheckpointerManager

async with CheckpointerManager() as manager:
    await manager.create_checkpointer()

    # Cleanup checkpoints older than 7 days
    deleted_count = await manager.cleanup_old_checkpoints(days=7)
    print(f"Deleted {deleted_count} old checkpoints")
```

### Custom Settings

```python
from deep_agent.agents.deep_agent import create_agent
from deep_agent.config.settings import Settings

# Override settings
settings = Settings(
    ENV="prod",
    GPT5_MODEL_NAME="gpt-5",
    GPT5_DEFAULT_REASONING_EFFORT="high",
    ENABLE_HITL=True
)

agent = await create_agent(settings=settings)
```

## Dependencies

### Internal Dependencies

- **`../services/llm_factory`** - LLM creation with GPT5Config and reasoning/verbosity controls
- **`../integrations/langsmith`** - Observability tracing setup via `setup_langsmith()`
- **`../models/gpt5`** - GPT-5 configuration models (GPT5Config, ReasoningEffort, Verbosity)
- **`../config/settings`** - Application settings (API keys, model configs, environment)
- **`../core/logging`** - Structured logging with contextual information
- **`../tools/web_search`** - Web search tool using Perplexity MCP client

### External Dependencies

- **`langgraph`** - LangGraph framework for stateful agent graphs
  - `CompiledStateGraph` - Compiled agent graph type
  - `langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver` - Async SQLite checkpointer
- **`deepagents`** - LangChain's DeepAgents high-level agent API
  - `create_deep_agent()` - Main agent creation function
- **`aiosqlite`** - Async SQLite database for checkpointer
- **`langchain`** - LangChain base utilities (imported transitively)

## Architecture Notes

### Layered Architecture

The agents module follows a four-layer architecture:

1. **Configuration Layer** (`prompts.py`, `prompts_variants.py`)
   - Defines system prompts, variants, and environment-specific behavior
   - Version tracking for prompt evolution monitoring
   - A/B testing infrastructure for prompt optimization

2. **Infrastructure Layer** (`checkpointer.py`, `reasoning_router.py`)
   - State persistence with checkpointers (SQLite → PostgreSQL migration path)
   - Reasoning effort optimization (Phase 0: static, Phase 1: dynamic)
   - Resource lifecycle management (async context managers)

3. **Agent Layer** (`deep_agent.py`)
   - Orchestrates layers 1-2 into complete agent instances
   - Integrates LLM factory, tools, checkpointer, and LangSmith tracing
   - Exposes clean API: `create_agent()` returns ready-to-use agent

4. **Sub-Agent Layer** (`sub_agents/`)
   - Specialized agents for delegation (Phase 1+)
   - Future: research-agent, code-review-agent, testing-agent

### Design Patterns

- **Factory Pattern**: `create_agent()` abstracts complex agent construction
- **Strategy Pattern**: Reasoning router selects reasoning effort strategy
- **Async Context Manager**: CheckpointerManager ensures resource cleanup
- **Singleton Pattern**: Settings accessed via `get_settings()` singleton
- **Builder Pattern**: GPT5Config builds LLM configuration incrementally

### Key Design Decisions

1. **Why AsyncSqliteSaver in Phase 0?**
   - Simple local development (no external database)
   - Fast iteration and testing
   - Migration path to PostgresSaver in Phase 1 (production-grade)

2. **Why separate prompts.py and prompts_variants.py?**
   - `prompts.py`: Production prompts with environment-specific appendices
   - `prompts_variants.py`: Experimental variants for A/B testing
   - Clear separation between stable (production) and experimental (optimization)

3. **Why reasoning_router.py returns MEDIUM in Phase 0?**
   - Phase 0 focuses on core functionality (agent creation, tools, HITL)
   - Dynamic routing requires complexity analysis (Phase 1 feature)
   - MEDIUM provides good balance for MVP testing

4. **Why LangSmith setup in create_agent()?**
   - Tracing must be configured before LLM/agent creation
   - Ensures all agent operations automatically traced
   - No manual tracing calls needed in application code

### Phase 0 Completeness

Phase 0 implementation is **complete** with:
- ✅ Agent creation with DeepAgents framework
- ✅ GPT-5 integration with reasoning effort control
- ✅ State persistence with AsyncSqliteSaver
- ✅ LangSmith tracing for observability
- ✅ Web search tool (Perplexity MCP)
- ✅ Environment-specific prompts (dev/prod)
- ✅ A/B testing infrastructure (prompt variants)
- ✅ HITL approval support (enabled via settings)

### Phase 1 Enhancements

Planned Phase 1 improvements:
- 🔄 Dynamic reasoning routing (trigger phrases, complexity analysis)
- 🔄 PostgreSQL checkpointer for production (AsyncPostgresSaver)
- 🔄 Sub-agent implementations (research, code review, testing)
- 🔄 Memory system integration (pgvector for semantic search)
- 🔄 Advanced prompt optimization (Opik auto-tuning)

## Related Documentation

### Architecture Documentation
- [Architecture Overview](../../docs/architecture/README.md) - High-level system architecture
- [Agent Architecture](../../docs/architecture/agents.md) - Detailed agent design
- [State Management](../../docs/architecture/checkpointing.md) - Checkpointer strategy

### API Documentation
- [API Endpoints](../../docs/api/endpoints.md) - FastAPI endpoints using agents
- [Agent API Reference](../../docs/api/agents.md) - Agent creation and invocation
- [Tool API Reference](../../docs/api/tools.md) - Custom tool implementations

### Development Guides
- [Development Setup](../../docs/development/setup.md) - Local environment setup
- [Testing Guide](../../docs/development/testing.md) - Testing strategies and examples
- [Contributing Guide](../../CONTRIBUTING.md) - Contribution guidelines

### External Documentation
- [LangGraph DeepAgents](https://github.com/langchain-ai/deepagents) - Official DeepAgents repository
- [LangGraph Checkpointing](https://langchain-ai.github.io/langgraph/how-tos/persistence/) - Checkpointer guide
- [LangSmith Tracing](https://docs.smith.langchain.com/tracing) - Observability documentation
- [GPT-5 Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide) - GPT-5 prompting best practices

## Testing

### Unit Tests

Located in `tests/unit/test_agents/`:

- `test_checkpointer.py` - Checkpointer creation, cleanup, resource management
- `test_reasoning_router.py` - Reasoning effort determination (Phase 0 baseline)
- `test_prompts.py` - Prompt selection, environment handling, versioning
- `test_prompts_variants.py` - Variant selection, metadata, A/B testing logic

Run unit tests:
```bash
pytest tests/unit/test_agents/ -v
```

### Integration Tests

Located in `tests/integration/test_agents/`:

- `test_deep_agent.py` - End-to-end agent creation with all components
- `test_agent_with_checkpointer.py` - State persistence across invocations
- `test_agent_with_tools.py` - Tool execution (web search, file system)
- `test_agent_variants.py` - A/B testing with different prompt variants

Run integration tests:
```bash
pytest tests/integration/test_agents/ -v
```

### E2E Tests

Located in `tests/e2e/test_complete_workflows/`:

- `test_basic_chat.py` - Simple chat interaction with streaming
- `test_hitl_workflow.py` - Human-in-the-loop approval flow
- `test_tool_usage.py` - Agent using file tools and web search
- `test_multi_turn.py` - Multi-turn conversation with state persistence

Run E2E tests:
```bash
pytest tests/e2e/ -v
```

### Coverage Requirements

Minimum coverage: **80%** (enforced in CI/CD)

Check coverage:
```bash
pytest tests/ --cov=deep_agent/agents --cov-report=html
open htmlcov/index.html
```

---

**Version:** 1.0.0 (Phase 0 Complete)
**Last Updated:** 2025-11-12
**Maintainers:** Deep Agent AGI Team
