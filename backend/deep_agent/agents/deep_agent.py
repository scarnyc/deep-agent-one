"""DeepAgent creation and configuration using LangChain's create_deep_agent API.

Model Configuration:
    - Primary: Gemini 3 Pro (Google) - fast, cost-effective
    - Fallback: GPT-5.1 (OpenAI) - reliable backup on errors

Uses ModelFallbackMiddleware from LangChain to automatically switch
to fallback model on rate limits, timeouts, or other errors.
"""

import traceback
from typing import Any

from deepagents import create_deep_agent
from langchain.agents.middleware import ModelFallbackMiddleware
from langgraph.graph.state import CompiledStateGraph

from deep_agent.agents.checkpointer import CheckpointerManager
from deep_agent.agents.prompts import get_agent_instructions
from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.logging import get_logger
from deep_agent.integrations.langsmith import setup_langsmith
from deep_agent.models.llm import (
    GeminiConfig,
    GPTConfig,
    ReasoningEffort,
    ThinkingLevel,
    Verbosity,
)
from deep_agent.services.llm_factory import create_gemini_llm, create_gpt_llm
from deep_agent.tools.web_search import web_search

logger = get_logger(__name__)


async def create_agent(
    settings: Settings | None = None,
    subagents: list[Any] | None = None,
    prompt_variant: str | None = None,
) -> CompiledStateGraph:
    """
    Create a DeepAgent with LangGraph using official create_deep_agent() API.

    This function wraps LangChain's create_deep_agent() with our configuration,
    LLM factory, and checkpointer integration for state persistence.

    Args:
        settings: Settings instance with configuration. If None, uses get_settings().
        subagents: Optional list of sub-agents for delegation. Defaults to None.
        prompt_variant: Optional prompt variant name for A/B testing.
                       Options: "control", "max_compression", "balanced", "conservative".
                       If None, uses environment-specific prompt (dev/prod).

    Returns:
        CompiledStateGraph configured with recursion_limit to prevent infinite loops,
        ready for invocation with checkpointer attached

    Raises:
        ValueError: If API key is missing or invalid, or prompt_variant is unknown
        OSError: If checkpointer database cannot be created
        RuntimeError: If graph compilation fails

    Example:
        >>> from deep_agent.agents.deep_agent import create_agent
        >>> agent = await create_agent()
        >>> result = await agent.ainvoke(
        ...     {"messages": [{"role": "user", "content": "Hello"}]},
        ...     {"configurable": {"thread_id": "user-123"}}
        ... )

    A/B Testing Example:
        >>> # Test with balanced variant
        >>> agent = await create_agent(prompt_variant="balanced")
        >>> # Test with max_compression variant
        >>> agent = await create_agent(prompt_variant="max_compression")

    File System Tools:
        DeepAgents includes these file system tools by default:
        - ls: List files in directory
        - read_file: Read file contents
        - write_file: Create new files
        - edit_file: Modify existing files
        - write_todos: Planning and todo management

    Custom Tools:
        - web_search: Search the web using Perplexity MCP

    HITL Support:
        Human-in-the-loop approval is built into DeepAgents.
        Configure via settings.ENABLE_HITL.
    """
    # Get settings
    if settings is None:
        settings = get_settings()

    # Configure LangSmith tracing for observability
    # Must be called before agent/LLM creation for automatic tracing
    setup_langsmith(settings)

    logger.info(
        "Creating DeepAgent with model fallback",
        primary_model=settings.GEMINI_MODEL_NAME,
        fallback_model=settings.GPT_MODEL_NAME,
        fallback_enabled=settings.ENABLE_MODEL_FALLBACK,
        hitl_enabled=settings.ENABLE_HITL,
        subagents_count=len(subagents) if subagents else 0,
    )

    # Create primary model (Gemini 3 Pro)
    gemini_config = GeminiConfig(
        model_name=settings.GEMINI_MODEL_NAME,
        temperature=settings.GEMINI_TEMPERATURE,
        thinking_level=ThinkingLevel(settings.GEMINI_THINKING_LEVEL),
        max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
    )

    try:
        primary_llm = create_gemini_llm(
            api_key=settings.GOOGLE_API_KEY,
            config=gemini_config,
        )
        logger.debug("Created Gemini LLM instance (primary)", model=gemini_config.model_name)
    except ValueError as e:
        logger.error("Failed to create primary LLM (Gemini)", error=str(e))
        raise

    # Create fallback model (GPT-5.1) and middleware
    middleware_list: list[Any] = []

    if settings.ENABLE_MODEL_FALLBACK and settings.OPENAI_API_KEY:
        gpt_config = GPTConfig(
            model_name=settings.GPT_MODEL_NAME,
            reasoning_effort=ReasoningEffort(settings.GPT_DEFAULT_REASONING_EFFORT),
            verbosity=Verbosity(settings.GPT_DEFAULT_VERBOSITY),
            max_tokens=settings.GPT_MAX_TOKENS,
        )

        try:
            fallback_llm = create_gpt_llm(
                api_key=settings.OPENAI_API_KEY,
                config=gpt_config,
            )
            middleware_list.append(ModelFallbackMiddleware(fallback_llm))
            logger.info(
                "Model fallback enabled",
                primary=settings.GEMINI_MODEL_NAME,
                fallback=settings.GPT_MODEL_NAME,
            )
        except ValueError as e:
            logger.warning(
                "Failed to create fallback LLM (GPT), continuing without fallback",
                error=str(e),
            )
    else:
        logger.info(
            "Model fallback disabled",
            enable_fallback=settings.ENABLE_MODEL_FALLBACK,
            has_openai_key=bool(settings.OPENAI_API_KEY),
        )

    # Create checkpointer for state persistence
    # Note: Checkpointer is disabled in test environment to prevent streaming hangs
    # Note: We don't use context manager here because the checkpointer needs
    # to stay open for the lifetime of the agent. The agent will manage the
    # checkpointer's lifecycle through its own cleanup mechanisms.
    checkpointer = None

    if settings.ENV != "test":
        checkpointer_manager = CheckpointerManager(settings=settings)
        try:
            checkpointer = await checkpointer_manager.create_checkpointer()
            logger.debug(
                "Created checkpointer",
                db_path=settings.CHECKPOINT_DB_PATH,
            )
        except (OSError, PermissionError) as e:
            logger.error(
                "Failed to create checkpointer",
                error=str(e),
                db_path=settings.CHECKPOINT_DB_PATH,
            )
            raise
    else:
        logger.info(
            "Checkpointer disabled for test environment",
            env=settings.ENV,
        )

    # Get system prompt
    # If prompt_variant specified, use variant for A/B testing
    # Otherwise, use environment-specific prompt (dev/prod)
    if prompt_variant:
        from deep_agent.agents.prompts_variants import select_prompt_variant

        try:
            variant_name, system_prompt = select_prompt_variant(variant_name=prompt_variant)
            logger.info(
                "Using prompt variant for A/B testing",
                variant=variant_name,
                prompt_length=len(system_prompt),
            )
        except ValueError as e:
            logger.error("Invalid prompt variant", variant=prompt_variant, error=str(e))
            raise
    else:
        # Default: environment-specific instructions
        system_prompt = get_agent_instructions(settings=settings)
        logger.debug(
            "Using environment-specific prompt",
            env=settings.ENV,
            prompt_length=len(system_prompt),
        )

    # Create DeepAgent using official API with ModelFallbackMiddleware
    try:
        logger.debug(
            "Calling create_deep_agent with parameters",
            model_type=type(primary_llm).__name__,
            tools_count=1,  # [web_search]
            system_prompt_length=len(system_prompt) if system_prompt else 0,
            subagents=subagents,
            has_checkpointer=checkpointer is not None,
            middleware_count=len(middleware_list),
        )

        compiled_graph = create_deep_agent(
            model=primary_llm,
            tools=[web_search],  # Custom tools in addition to built-in tools
            system_prompt=system_prompt,  # DeepAgents 0.2.0: parameter renamed from 'instructions'
            middleware=middleware_list,  # ModelFallbackMiddleware for Gemini -> GPT fallback
            subagents=subagents,
            checkpointer=checkpointer,
        )

        # Apply recursion limit to prevent infinite tool calling
        # LangGraph counts steps: 1 LLM call + 1 tool execution = 2 steps
        # So 12 tool calls (default) = 24 steps + 1 for initial call = 25 total
        max_tool_calls = settings.MAX_TOOL_CALLS_PER_INVOCATION
        recursion_limit = (max_tool_calls * 2) + 1

        agent = compiled_graph.with_config({"recursion_limit": recursion_limit})

        logger.info(
            "Successfully created DeepAgent with model fallback",
            primary_model=settings.GEMINI_MODEL_NAME,
            fallback_model=settings.GPT_MODEL_NAME if middleware_list else None,
            has_checkpointer=checkpointer is not None,
            subagents_enabled=subagents is not None and len(subagents) > 0,
            max_tool_calls=max_tool_calls,
            recursion_limit=recursion_limit,
        )

        return agent

    except Exception as e:
        # Log full traceback for debugging
        logger.error(
            "Failed to create DeepAgent",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
        )
        raise
