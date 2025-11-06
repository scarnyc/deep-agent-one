# Context Engineering Expert Agent

**Version:** 1.0.0
**Date:** 2025-11-06
**Status:** Phase 1 Feature (Productionization)
**Opik Package:** v2.2.1 (opik-optimizer) + v1.9.0 (opik)
**Benchmarks:** ✅ Verified Real Data

---

## Overview

The **Context Engineering Expert** is a specialized sub-agent built to optimize LLM prompts using GPT-5 best practices and Opik's optimization algorithms. It helps users systematically improve prompt quality, measure performance, and validate improvements through statistical testing.

### Key Features

- **GPT-5 Best Practices Analysis**: Automatic detection of contradictions, verbosity issues, and missing guidelines
- **6 Opik Optimization Algorithms**: HierarchicalReflective, FewShotBayesian, Evolutionary, MetaPrompt, GEPA, Parameter
- **Performance Evaluation**: Accuracy, latency, token cost, and quality metrics
- **A/B Testing**: Statistical comparison with effect size analysis
- **Dataset Generation**: Automated test case creation

---

## Architecture

### Components

```
backend/deep_agent/
├── agents/sub_agents/
│   ├── context_engineering_expert.py    # Agent implementation
│   └── prompts/
│       └── context_engineering_prompt.py # System prompt with algorithm guide
├── tools/
│   └── prompt_optimization.py           # 5 optimization tools
├── integrations/
│   └── opik_client.py                   # Opik SDK wrapper (all 6 algorithms)
└── config/
    └── settings.py                      # Opik configuration
```

### Tools Available

1. **analyze_prompt**: GPT-5 best practices checker
2. **optimize_prompt**: Multi-algorithm optimizer
3. **evaluate_prompt**: Performance metrics calculator
4. **create_evaluation_dataset**: Test case generator
5. **ab_test_prompts**: Statistical A/B testing

---

## Installation & Configuration

### 1. Dependencies

Already installed as part of Phase 1:

```toml
# pyproject.toml
opik = "^0.2.0"           # Prompt optimization platform
scipy = "^1.11.0"         # Statistical analysis
numpy = "^1.24.0"         # Numerical operations
```

### 2. Environment Variables

Add to `.env`:

```bash
# Opik Configuration
OPIK_API_KEY=your-opik-api-key           # Get from https://www.comet.com/opik
OPIK_WORKSPACE=your-workspace            # Your Opik workspace name
OPIK_PROJECT=deep-agent-agi              # Project for organizing experiments
```

### 3. Verify Installation

```bash
# Check Opik is installed
source venv/bin/activate
python -c "import opik; print(opik.__version__)"

# Check scipy and numpy
python -c "import scipy; import numpy; print('OK')"
```

---

## Usage

### Basic Usage: Analyze a Prompt

```python
from deep_agent.tools.prompt_optimization import analyze_prompt

prompt = """
You are a helpful AI assistant.
Use web search when needed.
"""

result = analyze_prompt(prompt, task_type="general")

print(f"Clarity Score: {result['clarity_score']}/100")
print(f"Issues Found: {len(result['issues'])}")
print(f"Violations: {result['best_practices_violations']}")
print(f"Recommendations: {result['recommendations']}")

# Output:
# Clarity Score: 80/100
# Issues Found: 2
# Violations: ['tool_usage: No parallel limits', 'tool_usage: No citation requirements']
# Recommendations: ['Add parallel tool call limits (max 3)', 'Require citations with URLs']
```

### Optimize a Prompt with Opik

```python
from deep_agent.tools.prompt_optimization import optimize_prompt

# Initial prompt
prompt = "You are a helpful assistant."

# Create evaluation dataset
dataset = [
    {"input": "What is AI?", "expected_output": "Artificial Intelligence..."},
    {"input": "Explain ML", "expected_output": "Machine Learning..."},
    # ...more examples
]

# Optimize using HierarchicalReflectiveOptimizer (Rank #1, 67.83% avg)
result = optimize_prompt(
    prompt=prompt,
    dataset=dataset,
    optimizer_type="hierarchical_reflective",
    max_trials=10,
)

print(f"Optimized Prompt:\n{result['optimized_prompt']}")
print(f"Score Improvement: {result['improvement']*100:.1f}%")
print(f"Final Score: {result['score']:.2f}")

# Output:
# Optimized Prompt:
# You are an expert AI assistant with systematic task decomposition...
# Score Improvement: 25.0%
# Final Score: 0.92
```

### A/B Test Two Prompts

```python
from deep_agent.tools.prompt_optimization import ab_test_prompts

prompt_a = "You are helpful."
prompt_b = "You are a systematic, thorough AI assistant."

dataset = [...]  # Evaluation dataset

result = ab_test_prompts(
    prompt_a=prompt_a,
    prompt_b=prompt_b,
    dataset=dataset,
    alpha=0.05,
)

print(f"Winner: Prompt {result['winner']}")
print(f"P-value: {result['p_value']:.4f}")
print(f"Effect Size: {result['effect_size']:.2f}")
print(f"Statistically Significant: {result['statistically_significant']}")

# Output:
# Winner: Prompt B
# P-value: 0.0123
# Effect Size: 0.68 (medium-to-large)
# Statistically Significant: True
```

### Use the Context Engineering Expert Agent

```python
from deep_agent.agents.sub_agents import get_context_engineering_expert

# Create agent
agent = await get_context_engineering_expert()

# Invoke with user query
result = await agent.ainvoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Analyze this prompt: You are a helpful assistant. Use tools when needed."
            }
        ]
    },
    {"configurable": {"thread_id": "user-123"}}
)

# Agent will use tools automatically to analyze and provide recommendations
print(result["messages"][-1]["content"])
```

---

## Opik Algorithm Selection Guide

The agent has access to 6 optimization algorithms. Choose based on your use case:

### 1. HierarchicalReflectiveOptimizer (RECOMMENDED)
**Rank:** #1 (67.83% avg)
**Best for:** Complex prompts requiring systematic refinement
**Benchmarks:** Arc: 92.70%, GSM8K: 28.00%, RagBench: 82.8%

**Use when:**
- Multi-step prompts
- Complex reasoning chains
- Systematic improvements needed

**Example:**
```python
optimize_prompt(prompt, dataset, optimizer_type="hierarchical_reflective", max_trials=10)
```

### 2. FewShotBayesianOptimizer
**Rank:** #2 (59.17% avg)
**Best for:** Optimizing few-shot examples
**Benchmarks:** Arc: 28.09%, GSM8K: 59.26%, RagBench: 90.15%

**Use when:**
- Chat models
- Few-shot prompts
- Example-based learning

### 3. EvolutionaryOptimizer
**Rank:** #3 (52.51% avg)
**Best for:** Discovering novel prompt structures
**Benchmarks:** Arc: 40.00%, GSM8K: 25.53%, RagBench: 92.00%

**Use when:**
- Exploring creative solutions
- Multi-objective goals (score vs. length)
- Unconstrained search

### 4. MetaPromptOptimizer
**Rank:** #4 (38.75% avg)
**Best for:** General refinement + MCP tool optimization
**Benchmarks:** Arc: 25.00%, GSM8K: 26.93%, RagBench: 64.31%

**Unique Feature:** **SUPPORTS MCP TOOL CALLING OPTIMIZATION**

**Use when:**
- Prompt clarity/wording improvements
- Structural improvements
- Agents with tools

**Example:**
```python
# Optimize prompt with MCP tools
tools = [{"name": "web_search", "description": "Search the web"}]
function_map = {"web_search": web_search_function}

optimize_prompt(
    prompt,
    dataset,
    optimizer_type="meta_prompt",
    tools=tools,
    function_map=function_map
)
```

### 5. GepaOptimizer
**Rank:** #5 (32.27% avg)
**Best for:** Single-turn tasks
**Benchmarks:** Arc: 6.55%, GSM8K: 26.08%, RagBench: 64.17%

**Requires:** `pip install gepa`

**Use when:**
- Simple, single-turn completions
- External GEPA package available

### 6. ParameterOptimizer
**Best for:** Tuning LLM parameters (temperature, top_p)
**Note:** No prompt text changes, only parameter optimization

**Use when:**
- Model behavior tuning
- No prompt modifications needed
- Optimizing temperature, top_p, etc.

---

## GPT-5 Best Practices Checklist

The `analyze_prompt` tool checks for:

### Agentic Behavior
- ✓ Task decomposition into subtasks
- ✓ Completion confirmation before terminating
- ✓ Autonomous information gathering
- ✓ Error recovery strategies

### Verbosity Control
- ✓ Appropriate verbosity for task type (research=high, chat=medium, quick=low)
- ✓ No contradictory verbosity instructions
- ✓ Clear when to be concise vs detailed

### Tool Usage
- ✓ Explicit tool usage guidelines
- ✓ Parallel tool call limits (max 3 for web search per Issue #113)
- ✓ Citation requirements for web searches: `[Source](URL)`
- ✓ Format specifications

### Structure
- ✓ XML-style tags for clarity (`<instructions>`, `<examples>`, etc.)
- ✓ Clear section headers
- ✓ Logical organization (general → specific)
- ✓ No contradictory instructions

### Completeness
- ✓ Defines success criteria
- ✓ Includes edge case handling
- ✓ Specifies error handling
- ✓ Provides examples where helpful

---

## Testing

### Unit Tests

```bash
# Run unit tests for prompt optimization tools
pytest tests/unit/test_tools/test_prompt_optimization.py -v

# Run with coverage
pytest tests/unit/test_tools/test_prompt_optimization.py --cov=backend/deep_agent/tools/prompt_optimization
```

### Integration Tests

```bash
# Run Opik integration tests
pytest tests/integration/test_opik_integration.py -m integration -v
```

### E2E Tests

```bash
# Run context-engineering-expert E2E tests
pytest tests/e2e/test_context_engineering_expert_e2e.py -m e2e -v
```

---

## Performance Metrics

The `evaluate_prompt` tool measures:

- **Accuracy**: Percentage of correct responses
- **Avg Latency (ms)**: Average response time
- **Total Tokens**: Token usage (cost estimation)
- **Quality Score**: Overall performance rating (0-1.0)

**Example Output:**
```json
{
  "accuracy": 0.89,
  "avg_latency_ms": 135.4,
  "total_tokens": 1450,
  "quality_score": 0.85
}
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'opik_optimizer'`

**Status:** ✅ RESOLVED (as of 2025-11-06)

The `opik-optimizer` package (v2.2.1) is now installed and working.

**Package Details:**
- **Separate package:** `opik-optimizer` ≠ `opik` (base package)
- **Requires:** `opik >= 1.7.17` (upgraded from 0.2.2 to 1.9.0)
- **Python constraint:** `>=3.11,<3.14`
- **GEPA included:** Installed automatically as dependency

**Verified Working Imports:**
```python
from opik_optimizer import (
    HierarchicalReflectiveOptimizer,
    FewShotBayesianOptimizer,
    EvolutionaryOptimizer,
    MetaPromptOptimizer,
    GepaOptimizer,
    ParameterOptimizer,
    ChatPrompt
)
```

All 6 optimizers confirmed working ✅

### Issue: GEPA optimizer no longer fails

**Status:** ✅ RESOLVED

GEPA (v0.0.19) is now automatically installed as a dependency of `opik-optimizer`. No separate installation needed.

### Issue: Low optimization scores

**Cause:** Insufficient evaluation dataset

**Fix:** Create larger dataset (minimum 10 examples recommended):
```python
from deep_agent.tools.prompt_optimization import create_evaluation_dataset

dataset = create_evaluation_dataset(
    description="Test cases for math calculation prompts",
    num_examples=20  # Increase for better optimization
)
```

---

## Integration with Main Agent

To use context-engineering-expert as a sub-agent:

```python
from deep_agent.agents.deep_agent import create_agent
from deep_agent.agents.sub_agents import get_context_engineering_expert

# Create context engineering expert
context_expert = await get_context_engineering_expert()

# Create main agent with sub-agents
main_agent = await create_agent(
    subagents=[context_expert]  # Delegation enabled
)

# Now main agent can delegate prompt optimization tasks
result = await main_agent.ainvoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Optimize my research agent's system prompt"
            }
        ]
    },
    {"configurable": {"thread_id": "user-123"}}
)
```

---

## Roadmap

### Phase 1 (Current)
- [x] Opik client wrapper (all 6 algorithms)
- [x] 5 prompt optimization tools
- [x] Context engineering expert agent
- [x] Comprehensive testing (unit, integration, E2E)
- [x] Documentation

### Phase 1.1 (Next)
- [ ] Replace placeholder optimizers with real Opik SDK when available
- [ ] Add prompt versioning and history tracking
- [ ] Integrate with LangSmith for optimization traces
- [ ] A/B testing infrastructure for production

### Phase 2
- [ ] Automated prompt regression testing
- [ ] Continuous prompt optimization in production
- [ ] Multi-objective optimization (cost vs. quality)
- [ ] Prompt template library

---

## References

- **Opik Documentation**: https://www.comet.com/docs/opik/agent_optimization/overview
- **GPT-5 Prompting Guide**: https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide
- **GPT-5 Best Practices**: Embedded in `GPT5_BEST_PRACTICES` constant (prompt_optimization.py)
- **Issue #113**: Parallel tool call limits (max 3) documented in prompts.py v1.1.0

---

## Support

For questions or issues:
1. Check troubleshooting section above
2. Review test files for usage examples
3. Consult `GITHUB_ISSUES.md` for known issues
4. File new issues in the project repository

---

**Last Updated:** 2025-11-06
**Maintainer:** Deep Agent AGI Team
