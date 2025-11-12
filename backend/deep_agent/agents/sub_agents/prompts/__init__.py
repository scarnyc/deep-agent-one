"""
System prompts for specialized sub-agents.

This module will contain system prompts for specialized sub-agents in Phase 1+.
Each sub-agent has a tailored system prompt that defines its role, capabilities,
and working style for specific task domains.

Planned Prompts (Phase 1+):
    - RESEARCH_AGENT_PROMPT: Multi-source research and synthesis instructions
    - CODE_REVIEW_AGENT_PROMPT: Code quality and security analysis guidelines
    - TESTING_AGENT_PROMPT: Test generation and validation strategies
    - DEBUGGING_AGENT_PROMPT: Error diagnosis and troubleshooting approaches
    - CONTEXT_ENGINEERING_AGENT_PROMPT: Prompt optimization best practices

Usage (Phase 1+):
    >>> from deep_agent.agents.sub_agents.prompts import RESEARCH_AGENT_PROMPT
    >>> from deepagents import create_deep_agent
    >>>
    >>> # Create sub-agent with specialized prompt
    >>> research_agent = create_deep_agent(
    ...     model=llm,
    ...     system_prompt=RESEARCH_AGENT_PROMPT,
    ...     tools=[web_search, wikipedia_search]
    ... )

Architecture:
    Sub-agent prompts follow the same patterns as main agent prompts:
    - Clear role definition and capabilities
    - Specific tool usage guidelines
    - Working style and best practices
    - HITL approval requirements for sensitive operations
    - Version tracking for prompt evolution

Phase 0 Status:
    This module is a placeholder in Phase 0. Sub-agent prompts will be added
    in Phase 1 based on specialized agent implementations.

Related Documentation:
    - Main Agent Prompts: ../../prompts.py
    - Prompt Variants: ../../prompts_variants.py
    - Sub-Agent Implementations: ../
"""

__all__ = []

