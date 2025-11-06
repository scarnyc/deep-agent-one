"""
Context Engineering Expert sub-agent.

Specialized agent for prompt optimization using Opik and GPT-5 best practices.
"""

import traceback
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from deepagents import create_deep_agent

from deep_agent.agents.sub_agents.prompts import get_context_engineering_prompt
from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.logging import get_logger
from deep_agent.integrations.langsmith import setup_langsmith
from deep_agent.models.gpt5 import GPT5Config, ReasoningEffort, Verbosity
from deep_agent.services.llm_factory import create_gpt5_llm
from deep_agent.tools.prompt_optimization import (
    ab_test_prompts,
    analyze_prompt,
    create_evaluation_dataset,
    evaluate_prompt,
    optimize_prompt,
)

logger = get_logger(__name__)


async def create_context_engineering_expert(
    settings: Settings | None = None,
) -> CompiledStateGraph:
    """
    Create a Context Engineering Expert agent using DeepAgents.

    This specialized agent helps users optimize LLM prompts using:
    - GPT-5 best practices analysis
    - Opik's 6 optimization algorithms
    - Statistical A/B testing
    - Performance evaluation metrics

    Args:
        settings: Settings instance with configuration. If None, uses get_settings().

    Returns:
        CompiledStateGraph ready for invocation

    Raises:
        ValueError: If API key is missing or invalid
        RuntimeError: If graph compilation fails

    Example:
        >>> from deep_agent.agents.sub_agents.context_engineering_expert import (
        ...     create_context_engineering_expert
        ... )
        >>> agent = await create_context_engineering_expert()
        >>> result = await agent.ainvoke(
        ...     {"messages": [{"role": "user", "content": "Analyze this prompt: ..."}]},
        ...     {"configurable": {"thread_id": "user-123"}}
        ... )

    Available Tools:
        - analyze_prompt: GPT-5 best practices analysis
        - optimize_prompt: Multi-algorithm optimization (Opik)
        - evaluate_prompt: Performance metrics (accuracy, latency, cost)
        - create_evaluation_dataset: Test case generation
        - ab_test_prompts: Statistical A/B testing

    Algorithm Selection:
        The agent has access to 6 Opik optimization algorithms:
        1. HierarchicalReflectiveOptimizer (Rank #1, 67.83%)
        2. FewShotBayesianOptimizer (Rank #2, 59.17%)
        3. EvolutionaryOptimizer (Rank #3, 52.51%)
        4. MetaPromptOptimizer (Rank #4, 38.75%) - Supports MCP tools
        5. GepaOptimizer (Rank #5, 32.27%)
        6. ParameterOptimizer - LLM parameter tuning

    LangSmith Tracing:
        All operations are traced via LangSmith for observability.
        Configure via settings.LANGSMITH_API_KEY.
    """
    # Get settings
    if settings is None:
        settings = get_settings()

    # Configure LangSmith tracing for observability
    # Must be called before agent/LLM creation for automatic tracing
    setup_langsmith(settings)

    logger.info(
        "Creating Context Engineering Expert agent",
        model=settings.GPT5_MODEL_NAME,
        reasoning_effort=settings.GPT5_DEFAULT_REASONING_EFFORT,
    )

    # Create LLM using factory
    # Use high reasoning effort for complex prompt analysis
    config = GPT5Config(
        model_name=settings.GPT5_MODEL_NAME,
        reasoning_effort=ReasoningEffort.HIGH,  # Complex analysis requires deep reasoning
        verbosity=Verbosity.MEDIUM,  # Balanced explanations
        max_tokens=settings.GPT5_MAX_TOKENS,
        temperature=0.3,  # Lower temperature for more consistent analysis
    )

    try:
        llm = create_gpt5_llm(
            api_key=settings.OPENAI_API_KEY,
            config=config,
        )
        logger.debug(
            "Created GPT-5 LLM instance for context engineering",
            model=config.model_name,
            reasoning_effort=config.reasoning_effort.value,
        )
    except ValueError as e:
        logger.error("Failed to create LLM for context engineering expert", error=str(e))
        raise

    # Get system prompt
    system_prompt = get_context_engineering_prompt()

    # Define tools for prompt optimization
    tools = [
        analyze_prompt,
        optimize_prompt,
        evaluate_prompt,
        create_evaluation_dataset,
        ab_test_prompts,
    ]

    # Create DeepAgent using official API
    try:
        logger.debug(
            "Calling create_deep_agent for context engineering expert",
            model_type=type(llm).__name__,
            tools_count=len(tools),
            system_prompt_length=len(system_prompt),
        )

        compiled_graph = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
            subagents=None,  # Context engineering expert does not delegate
            checkpointer=None,  # Sub-agents typically don't need state persistence
        )

        logger.info(
            "Successfully created Context Engineering Expert agent",
            tools_enabled=len(tools),
        )

        return compiled_graph

    except Exception as e:
        # Log full traceback for debugging
        logger.error(
            "Failed to create Context Engineering Expert agent",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
        )
        raise


# Singleton instance for reuse
_context_engineering_expert: CompiledStateGraph | None = None


async def get_context_engineering_expert(
    settings: Settings | None = None,
) -> CompiledStateGraph:
    """
    Get or create singleton Context Engineering Expert agent.

    Args:
        settings: Optional settings. If None, uses get_settings().

    Returns:
        CompiledStateGraph instance (cached after first call)
    """
    global _context_engineering_expert

    if _context_engineering_expert is None:
        _context_engineering_expert = await create_context_engineering_expert(
            settings=settings
        )

    return _context_engineering_expert
