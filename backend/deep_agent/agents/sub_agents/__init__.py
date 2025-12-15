"""
Sub-agents for specialized task delegation.

This module will contain specialized agent implementations for the DeepAgents
framework in Phase 1 and beyond. Sub-agents allow the main DeepAgent to delegate
specific types of tasks to agents with specialized instructions and tools.

Planned Sub-Agents (Phase 1+):
    - research-agent: Deep research with multi-source synthesis
    - code-review-agent: Code quality analysis and security review
    - testing-agent: Test generation and validation
    - debugging-agent: Error diagnosis and resolution strategies

Usage (Phase 1+):
    >>> from deep_agent.agents.sub_agents.research_agent import create_research_agent
    >>> from deep_agent.agents.deep_agent import create_agent
    >>>
    >>> # Create main agent with sub-agents
    >>> research_subagent = await create_research_agent()
    >>> main_agent = await create_agent(subagents=[research_subagent])
    >>>
    >>> # Agent automatically delegates research tasks to research-agent
    >>> result = await main_agent.ainvoke({
    ...     "messages": [{"role": "user", "content": "Research quantum computing"}]
    ... })

Architecture:
    Sub-agents follow the same patterns as the main DeepAgent:
    - System prompts in sub_agents/prompts/
    - Specialized tools for domain-specific tasks
    - Same checkpointer for state persistence
    - LangSmith tracing for observability

Phase 0 Status:
    This module is a placeholder in Phase 0. Sub-agent implementations will be
    added in Phase 1 based on user needs and usage patterns.

Related Documentation:
    - Main Agent: ../deep_agent.py
    - Agent Prompts: ../prompts.py
    - Testing: ../../../../tests/integration/test_sub_agents/
"""

__all__ = []
