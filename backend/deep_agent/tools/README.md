# Tools

## Purpose

Agent tools that extend agent capabilities with file system operations, web search, and prompt optimization utilities.

Tools are implemented as LangChain tools decorated with `@tool` and automatically registered with DeepAgents. The LLM selects tools dynamically based on task requirements.

## Key Files

- `__init__.py` - Tool exports for agent registration
- `web_search.py` - Perplexity web search tool for current information retrieval
- `prompt_optimization.py` - Suite of 5 tools for context engineering and prompt optimization

## Usage

### Web Search Tool

The web search tool provides real-time information retrieval via the Perplexity MCP client.

```python
from deep_agent.tools import web_search

# Async invocation (recommended)
result = await web_search.ainvoke({
    "query": "latest developments in AI agents",
    "max_results": 5
})
print(result)
```

**Output Format:**
```
Found 5 sources for "latest developments in AI agents":

1. AI Agents in 2025: The Future of Automation
   https://example.com/ai-agents-2025
   Recent advancements in autonomous AI agents show significant progress...

2. Deep Learning for Agentic Systems
   https://research.com/deep-agents
   New frameworks enable agents to reason and plan more effectively...
```

**Features:**
- Automatic query sanitization for security
- Rate limiting (10 requests per minute)
- Retry logic with exponential backoff (3 attempts)
- Timeout protection (30 seconds)
- Graceful error handling (returns error messages, not exceptions)
- Task cancellation support (handles client disconnects)

### Prompt Optimization Tools

Five tools for analyzing, optimizing, and validating prompts using Opik and GPT-5 best practices.

#### 1. analyze_prompt - GPT-5 Best Practices Analysis

Analyzes prompt structure against GPT-5 prompting guidelines.

```python
from deep_agent.tools import analyze_prompt

result = analyze_prompt(
    prompt="You are a helpful coding assistant.",
    task_type="code_gen"
)

print(result["clarity_score"])         # 0-100 rating
print(result["issues"])                # List of identified problems
print(result["recommendations"])       # Specific improvements
print(result["best_practices_violations"])  # GPT-5 guideline violations
```

**Checks:**
- Agentic behavior (task decomposition, completion confirmation)
- Clarity and structure (explicit instructions, XML-style sections)
- Verbosity control (task-appropriate detail level)
- Tool usage guidelines (parallel limits, citations)
- Contradiction detection (conflicting instructions)

#### 2. optimize_prompt - Opik-Powered Optimization

Optimizes prompt using Opik's 6 optimization algorithms.

```python
from deep_agent.tools import optimize_prompt

dataset = [
    {"input": "What is 2+2?", "expected_output": "4"},
    {"input": "What is 5+7?", "expected_output": "12"},
]

result = optimize_prompt(
    prompt="You are a math assistant.",
    dataset=dataset,
    optimizer_type="meta_prompt",  # or hierarchical_reflective, evolutionary, etc.
    max_trials=10
)

print(result["optimized_prompt"])  # Improved prompt
print(result["improvement"])       # Score improvement (%)
print(result["score"])            # Final performance score
```

**Available Algorithms:**
- `meta_prompt` - Meta-prompting with self-reflection
- `hierarchical_reflective` - Multi-level refinement (default, best for most tasks)
- `evolutionary` - Genetic algorithm approach
- `monte_carlo` - Random sampling with best selection
- `basic` - Simple iterative improvement
- `few_shot` - Example-based optimization

#### 3. evaluate_prompt - Performance Metrics

Evaluates prompt performance with quantitative metrics.

```python
from deep_agent.tools import evaluate_prompt

metrics = evaluate_prompt(
    prompt="You are a friendly assistant.",
    dataset=dataset,
    metrics=["accuracy", "latency", "cost"]
)

print(metrics["accuracy"])      # Task completion rate (0-1)
print(metrics["latency"])       # Average response time (seconds)
print(metrics["cost"])          # Token usage
print(metrics["quality_score"]) # Overall rating (0-100)
```

#### 4. create_evaluation_dataset - Test Case Generation

Generates evaluation datasets from task descriptions.

```python
from deep_agent.tools import create_evaluation_dataset

dataset = create_evaluation_dataset(
    task_description="Math word problems for grade 3",
    num_examples=20
)

print(len(dataset))      # 20
print(dataset[0])        # {"input": "...", "expected_output": "..."}
```

#### 5. ab_test_prompts - Statistical A/B Testing

Performs statistical comparison between two prompt variants.

```python
from deep_agent.tools import ab_test_prompts

result = ab_test_prompts(
    prompt_a="You are helpful.",
    prompt_b="You are an expert assistant with deep knowledge.",
    dataset=dataset,
    alpha=0.05  # Significance level
)

print(result["winner"])                    # "A", "B", or "tie"
print(result["p_value"])                   # Statistical significance
print(result["effect_size"])               # Cohen's d
print(result["statistically_significant"]) # True/False
print(result["metrics_comparison"])        # Detailed comparison
```

### Registering Tools with Agent

Tools are automatically registered via DeepAgents initialization:

```python
from deep_agent.agents import create_agent
from deep_agent.tools import web_search, analyze_prompt

# Create agent (tools auto-registered from imports in agents/core.py)
agent = await create_agent()

# Agent will dynamically select tools based on task
response = await agent.ainvoke({"messages": [("user", "Search for AI news")]})
```

## Tool Schema

Each tool defines:

### Name
Unique identifier used by LLM for tool selection.

### Description
Natural language description used by LLM to determine when to use the tool. Should be clear and specific.

### Input Schema
Defined via function parameters with type hints. LangChain automatically generates JSON schema.

```python
@tool
async def web_search(
    query: str,           # Required: search query
    max_results: int = 5  # Optional: result limit
) -> str:
    """Search the web for information..."""
    pass
```

### Output Schema
Documented in docstring. Tools return:
- **Success:** Formatted string with results
- **Error:** Error message string (tools do NOT raise exceptions to agent)

## Available Tools

### web_search
**Purpose:** Search the web using Perplexity MCP
**Input:** `query` (str), `max_results` (int, default=5)
**Output:** Formatted search results with titles, URLs, snippets
**Use Cases:** Current events, fact-checking, research, up-to-date information

### analyze_prompt
**Purpose:** Analyze prompt against GPT-5 best practices
**Input:** `prompt` (str), `task_type` (str, default="general")
**Output:** Dict with issues, violations, recommendations, scores
**Use Cases:** Prompt review, quality assessment, optimization preparation

### optimize_prompt
**Purpose:** Optimize prompt using Opik algorithms
**Input:** `prompt` (str), `dataset` (List[Dict]), `optimizer_type` (str), `max_trials` (int)
**Output:** Dict with optimized prompt, score, improvement percentage
**Use Cases:** Improving prompt performance, reducing token costs, increasing accuracy

### evaluate_prompt
**Purpose:** Evaluate prompt performance metrics
**Input:** `prompt` (str), `dataset` (List[Dict]), `metrics` (List[str])
**Output:** Dict with accuracy, latency, cost, quality_score
**Use Cases:** Benchmarking prompts, performance validation, A/B test preparation

### create_evaluation_dataset
**Purpose:** Generate test cases from task description
**Input:** `task_description` (str), `num_examples` (int, default=20)
**Output:** List of {"input": ..., "expected_output": ...} dicts
**Use Cases:** Creating evaluation datasets, test case generation

### ab_test_prompts
**Purpose:** Statistical A/B testing for prompts
**Input:** `prompt_a` (str), `prompt_b` (str), `dataset` (List[Dict]), `alpha` (float)
**Output:** Dict with winner, p_value, effect_size, metrics_comparison
**Use Cases:** Prompt comparison, statistical validation, optimization verification

## Adding New Tools

To add a new tool:

1. **Create tool file** in `backend/deep_agent/tools/`
2. **Implement tool** with `@tool` decorator
3. **Export tool** in `__init__.py`
4. **Register with agent** (automatic via imports in `agents/core.py`)

Example:

```python
# backend/deep_agent/tools/my_new_tool.py
from langchain_core.tools import tool
from deep_agent.core.logging import get_logger

logger = get_logger(__name__)

@tool
async def my_custom_tool(query: str) -> str:
    """
    Brief description for LLM tool selection.

    Detailed description of what the tool does, when to use it,
    and what it returns.

    Args:
        query: Description of input parameter

    Returns:
        Description of output format

    Example:
        >>> result = await my_custom_tool.ainvoke("test")
        >>> print(result)
        "Result: ..."
    """
    logger.info("Tool invoked", query=query)

    try:
        # Implementation
        result = do_something(query)
        return f"Success: {result}"

    except Exception as e:
        # Return error message (do NOT raise)
        logger.error("Tool failed", error=str(e))
        return f"Error: {str(e)}"
```

```python
# backend/deep_agent/tools/__init__.py
from deep_agent.tools.my_new_tool import my_custom_tool

__all__ = [
    "web_search",
    "my_custom_tool",  # Add to exports
]
```

**Best Practices:**
- Use descriptive docstrings (LLM uses these for tool selection)
- Return error messages instead of raising exceptions
- Log all tool invocations and errors
- Include usage examples in docstrings
- Use type hints for input parameters
- Handle async operations properly (`async def`, `await`)
- Implement timeout protection for external API calls
- Add retry logic for transient failures

## Dependencies

### Internal
- `../integrations/mcp_clients/` - MCP client implementations (Perplexity)
- `../integrations/opik_client.py` - Opik optimization client
- `../config/settings.py` - Configuration management
- `../core/logging.py` - Structured logging

### External
- `langchain_core.tools` - Tool decorator and base classes
- `langchain_openai` - OpenAI LLM integration for prompt evaluation
- `opik` - Prompt optimization framework
- `scipy` - Statistical testing (t-test for A/B testing)
- `numpy` - Numerical operations

## Related Documentation

- [Agents](../agents/README.md) - Agent initialization and execution
- [Integrations](../integrations/README.md) - MCP clients and external services
- [Configuration](../config/README.md) - Settings and environment management

## Testing

### Unit Tests
Location: `tests/unit/test_tools/`

```bash
# Run all tool tests
pytest tests/unit/test_tools/ -v

# Test specific tool
pytest tests/unit/test_tools/test_web_search.py -v
```

### Integration Tests
Location: `tests/integration/test_tools/`

```bash
# Run integration tests (requires MCP servers)
pytest tests/integration/test_tools/ -v
```

### Test Coverage
Maintain >80% test coverage for all tool implementations.

```bash
# Check tool coverage
pytest tests/unit/test_tools/ --cov=backend/deep_agent/tools --cov-report=term
```

## Error Handling

All tools follow consistent error handling:

1. **Catch exceptions** - Never let exceptions propagate to agent
2. **Return error messages** - Return descriptive error strings
3. **Log errors** - Use structured logging for debugging
4. **Provide context** - Include query/input in error messages

Example:
```python
try:
    result = perform_operation()
    return f"Success: {result}"
except ValueError as e:
    logger.warning("Validation failed", error=str(e))
    return f"Validation error: {str(e)}"
except Exception as e:
    logger.error("Unexpected error", error=str(e))
    return f"Unexpected error: {str(e)}"
```

## Performance Considerations

### Web Search Tool
- **Rate limit:** 10 requests/minute (enforced by Perplexity client)
- **Timeout:** 30 seconds per request
- **Retries:** 3 attempts with exponential backoff
- **Caching:** Not implemented (consider for Phase 2)

### Prompt Optimization Tools
- **Latency:** 10-60 seconds depending on algorithm and dataset size
- **Token usage:** High (runs multiple LLM calls for optimization)
- **Cost estimation:** ~$0.10-1.00 per optimization run (depends on dataset size)
- **Recommendation:** Use smaller datasets (10-20 examples) for faster iteration

## Security

### Input Validation
- Query sanitization (web search)
- Schema validation (all tools)
- Rate limiting (external API calls)

### API Key Management
- Never expose API keys in tool responses
- Use environment variables for credentials
- Rotate keys regularly

### Error Messages
- Don't leak sensitive information in error messages
- Sanitize file paths before logging
- Redact API keys from logs

## Future Enhancements (Phase 2)

- [ ] File system tools (read, write, edit, ls) from DeepAgents
- [ ] Code execution tools (sandboxed Python/JavaScript)
- [ ] Email tools (Gmail API integration)
- [ ] Calendar tools (Google Calendar API)
- [ ] Database query tools (PostgreSQL, pgvector)
- [ ] Image generation tools (DALL-E integration)
- [ ] Custom MCP servers (fastmcp)

## References

- [LangChain Tool Documentation](https://python.langchain.com/docs/modules/tools/)
- [DeepAgents Repository](https://github.com/langchain-ai/deepagents)
- [Perplexity MCP](https://github.com/perplexityai/modelcontextprotocol)
- [Opik Documentation](https://www.comet.com/docs/opik/)
- [GPT-5 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)
