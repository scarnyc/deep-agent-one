"""
Agents module for DeepAgent framework.

This module provides agent implementations, configuration, and state management
for the Deep Agent AGI system. It includes the core DeepAgent creation logic,
checkpointer management for state persistence, reasoning routers, and prompt
engineering utilities.

Key Components:
    - deep_agent.py: Main DeepAgent creation using LangChain's create_deep_agent API
    - checkpointer.py: State persistence with SQLite/PostgreSQL checkpointers
    - reasoning_router.py: Routing logic for GPT-5 reasoning effort optimization
    - prompts.py: Environment-specific system prompts with versioning
    - prompts_variants.py: A/B testing variants for prompt optimization
    - sub_agents/: Specialized sub-agent implementations (Phase 1+)

Usage:
    >>> from deep_agent.agents.deep_agent import create_agent
    >>> from deep_agent.agents.checkpointer import CheckpointerManager
    >>>
    >>> # Create agent with default settings
    >>> agent = await create_agent()
    >>>
    >>> # Use checkpointer for state persistence
    >>> async with CheckpointerManager() as manager:
    ...     checkpointer = await manager.create_checkpointer()
    ...     agent = await create_agent()  # checkpointer auto-attached
    >>>
    >>> # A/B test with prompt variants
    >>> agent = await create_agent(prompt_variant="balanced")

Architecture:
    The agents module follows a layered architecture:
    1. Configuration Layer: prompts.py, prompts_variants.py
    2. Infrastructure Layer: checkpointer.py, reasoning_router.py
    3. Agent Layer: deep_agent.py (orchestrates layers 1-2)
    4. Sub-Agent Layer: sub_agents/ (specialized agents)

Dependencies:
    - Internal: ../services/llm_factory, ../integrations/langsmith, ../models/gpt5
    - External: langgraph, langchain, deepagents, aiosqlite

Related Documentation:
    - Architecture: ../../docs/architecture/
    - API Reference: ../../docs/api/
    - Testing: ../../../tests/unit/test_agents/, ../../../tests/integration/test_agents/
"""

__all__: list[str] = []
