# Sub-Agents

## Purpose
Specialized sub-agents for delegation from the main DeepAgent. Planned for Phase 1 implementation using LangGraph's sub-agent pattern.

## Current Status
**Phase 0**: Placeholder directory structure with comprehensive docstrings
**Phase 1**: Full implementation planned

## Planned Sub-Agents

### General-Purpose Sub-Agent
- Research and multi-step tasks
- File operations and code generation
- Autonomous task completion

### Specialized Sub-Agents (Future)

#### Code Review Expert
- Code quality analysis
- Security vulnerability detection
- Integration with TheAuditor
- Best practices enforcement
- Type safety validation

#### Testing Expert
- Test generation and validation
- Coverage analysis
- Test pattern verification (AAA pattern)
- Edge case identification
- Mock usage recommendations

#### Documentation Expert
- Docstring generation and validation
- API documentation creation
- User guide authoring
- Code comment improvement

#### Debugging Expert
- Error diagnosis and triage
- Stack trace analysis
- Resolution strategy recommendations
- Root cause identification

## Architecture

### Sub-Agent Pattern
```python
from deepagents import create_deep_agent

# Main agent with sub-agent delegation
main_agent = create_deep_agent(
    subagents=[general_purpose_agent, code_review_agent]
)

# Sub-agents are invoked automatically based on task
```

### Delegation Strategy
1. Main agent analyzes task complexity and type
2. Delegates to specialized sub-agent when appropriate
3. Sub-agent reports back to main agent with results
4. Main agent synthesizes final response for user

### Communication Flow
```
User Request
    ↓
Main Agent (analyze task)
    ↓
[Delegate to Sub-Agent?]
    ↓
Sub-Agent (specialized execution)
    ↓
Return Results
    ↓
Main Agent (synthesize response)
    ↓
User Response
```

## Directory Structure
```
sub_agents/
├── __init__.py          # Sub-agent exports (Phase 1)
├── prompts/             # Sub-agent system prompts
│   ├── __init__.py      # Prompt exports (Phase 1)
│   └── [prompt files]   # Phase 1
├── README.md            # This file
└── [agent modules]      # Phase 1
```

## Implementation Roadmap

### Phase 1
- [ ] Implement general-purpose sub-agent
- [ ] Add code review sub-agent (integrate with TheAuditor)
- [ ] Add testing sub-agent (pytest pattern validation)
- [ ] Create sub-agent prompts
- [ ] Add delegation logic
- [ ] Test multi-agent workflows
- [ ] Add HITL approval for sub-agent operations

### Phase 2
- [ ] Add debugging sub-agent
- [ ] Add documentation sub-agent
- [ ] Implement sub-agent memory (shared context)
- [ ] Add sub-agent coordination patterns (parallel execution)
- [ ] Add sub-agent performance tracking
- [ ] Implement sub-agent A/B testing

## Sub-Agent Configuration

Each sub-agent will follow this configuration pattern:

```python
# Example: code_review_agent.py
from deepagents import create_deep_agent
from .prompts import CODE_REVIEW_AGENT_PROMPT

async def create_code_review_agent(
    llm,
    tools=None,
    checkpointer=None
):
    """Create specialized code review agent.

    Args:
        llm: Language model instance
        tools: Additional tools for code review
        checkpointer: State persistence checkpointer

    Returns:
        Configured code review agent
    """
    default_tools = [
        run_security_scan,  # TheAuditor integration
        analyze_code_quality,
        check_type_hints,
        validate_tests
    ]

    all_tools = default_tools + (tools or [])

    return create_deep_agent(
        model=llm,
        system_prompt=CODE_REVIEW_AGENT_PROMPT,
        tools=all_tools,
        checkpointer=checkpointer
    )
```

## Dependencies
- **Internal**:
  - `../deep_agent.py` - Main agent implementation
  - `../prompts.py` - Shared prompt utilities
  - `../../tools/` - Shared tools
- **External**:
  - `langchain` - Core framework
  - `langgraph` - DeepAgents pattern

## Related Documentation
- [Agents](../README.md)
- [DeepAgents docs](https://github.com/langchain-ai/deepagents)
- [Main Agent Implementation](../deep_agent.py)
- [System Prompts](../prompts.py)
- [Prompt Variants](../prompts_variants.py)

## Testing

### Unit Tests (Phase 1)
```
tests/unit/test_agents/test_sub_agents/
├── test_code_review_agent.py
├── test_testing_agent.py
└── test_debugging_agent.py
```

### Integration Tests (Phase 1)
```
tests/integration/test_agents/test_sub_agents/
├── test_agent_delegation.py
├── test_multi_agent_workflow.py
└── test_sub_agent_coordination.py
```

### Test Coverage Requirements
- Minimum 80% coverage for all sub-agents
- Test delegation logic thoroughly
- Test HITL approval workflows
- Test sub-agent communication patterns
- Test error handling and fallback strategies

## Monitoring & Observability

All sub-agents will be instrumented with LangSmith tracing:
- Track delegation decisions
- Monitor sub-agent execution time
- Log tool usage by sub-agents
- Track success/failure rates
- Measure token usage per sub-agent

## Example Usage (Phase 1+)

### Code Review Sub-Agent
```python
from deep_agent.agents.sub_agents import create_code_review_agent
from deep_agent.agents.deep_agent import create_agent

# Create sub-agent
code_reviewer = await create_code_review_agent(llm)

# Create main agent with sub-agent
main_agent = await create_agent(
    subagents=[code_reviewer]
)

# Main agent automatically delegates code review tasks
result = await main_agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "Review this code for security issues: [code]"
    }]
})
```

## Best Practices

1. **Clear Role Definition**: Each sub-agent has a specific, well-defined role
2. **Tool Specialization**: Sub-agents use domain-specific tools
3. **HITL Integration**: Sensitive operations require human approval
4. **State Persistence**: Use checkpointer for long-running tasks
5. **Observability**: All sub-agent operations traced with LangSmith
6. **Error Handling**: Graceful fallback when delegation fails
7. **Testing**: Comprehensive unit and integration tests
8. **Documentation**: Clear docstrings and usage examples

## Performance Considerations

- **Delegation Overhead**: Main agent decides if delegation is worth the latency
- **Token Usage**: Sub-agents may use more tokens (specialized prompts)
- **Parallel Execution**: Some sub-agents can run in parallel (Phase 2)
- **Caching**: Common sub-agent results can be cached (Phase 2)

## Security

- Sub-agents inherit security context from main agent
- HITL approval required for sensitive operations
- TheAuditor integration for code review sub-agent
- No secrets in sub-agent prompts
- Audit logs for all sub-agent actions

## Future Enhancements (Phase 3+)

- **Dynamic Sub-Agent Creation**: Create specialized sub-agents on-demand
- **Sub-Agent Learning**: Improve delegation based on past performance
- **Multi-Agent Coordination**: Complex workflows with multiple sub-agents
- **Sub-Agent Marketplace**: Community-contributed specialized agents
- **Cross-Agent Memory**: Shared context and learnings across sub-agents
