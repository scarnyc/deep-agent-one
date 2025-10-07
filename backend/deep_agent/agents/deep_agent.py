"""DeepAgent creation and configuration using LangChain's create_deep_agent API."""

from typing import Any

from langgraph.graph.state import CompiledStateGraph

from deepagents import create_deep_agent

from backend.deep_agent.agents.checkpointer import CheckpointerManager
from backend.deep_agent.agents.prompts import get_agent_instructions
from backend.deep_agent.config.settings import Settings, get_settings
from backend.deep_agent.core.logging import get_logger
from backend.deep_agent.integrations.langsmith import setup_langsmith
from backend.deep_agent.models.gpt5 import GPT5Config, ReasoningEffort, Verbosity
from backend.deep_agent.services.llm_factory import create_gpt5_llm
from backend.deep_agent.tools.web_search import web_search

logger = get_logger(__name__)


async def create_agent(
    settings: Settings | None = None,
    subagents: list[Any] | None = None,
) -> CompiledStateGraph:
    """
    Create a DeepAgent with LangGraph using official create_deep_agent() API.

    This function wraps LangChain's create_deep_agent() with our configuration,
    LLM factory, and checkpointer integration for state persistence.

    Args:
        settings: Settings instance with configuration. If None, uses get_settings().
        subagents: Optional list of sub-agents for delegation. Defaults to None.

    Returns:
        CompiledStateGraph ready for invocation with checkpointer attached

    Raises:
        ValueError: If API key is missing or invalid
        OSError: If checkpointer database cannot be created
        RuntimeError: If graph compilation fails

    Example:
        >>> from backend.deep_agent.agents.deep_agent import create_agent
        >>> agent = await create_agent()
        >>> result = await agent.ainvoke(
        ...     {"messages": [{"role": "user", "content": "Hello"}]},
        ...     {"configurable": {"thread_id": "user-123"}}
        ... )

    Built-in Tools:
        DeepAgents includes these tools by default:
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
        "Creating DeepAgent",
        model=settings.GPT5_MODEL_NAME,
        reasoning_effort=settings.GPT5_DEFAULT_REASONING_EFFORT,
        hitl_enabled=settings.ENABLE_HITL,
        subagents_count=len(subagents) if subagents else 0,
    )

    # Create LLM using factory
    config = GPT5Config(
        model_name=settings.GPT5_MODEL_NAME,
        reasoning_effort=ReasoningEffort(settings.GPT5_DEFAULT_REASONING_EFFORT),
        verbosity=Verbosity(settings.GPT5_DEFAULT_VERBOSITY),
        max_tokens=settings.GPT5_MAX_TOKENS,
        temperature=settings.GPT5_TEMPERATURE,
    )

    try:
        llm = create_gpt5_llm(
            api_key=settings.OPENAI_API_KEY,
            config=config,
        )
        logger.debug("Created GPT-5 LLM instance", model=config.model_name)
    except ValueError as e:
        logger.error("Failed to create LLM", error=str(e))
        raise

    # Create checkpointer for state persistence
    async with CheckpointerManager(settings=settings) as checkpointer_manager:
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

        # Get environment-specific system instructions
        instructions = get_agent_instructions(settings=settings)

        # Create DeepAgent using official API
        try:
            compiled_graph = create_deep_agent(
                model=llm,
                tools=[web_search],  # Custom tools in addition to built-in tools
                instructions=instructions,
                subagents=subagents,
                checkpointer=checkpointer,
            )

            logger.info(
                "Successfully created and compiled DeepAgent",
                has_checkpointer=True,
                subagents_enabled=subagents is not None and len(subagents) > 0,
            )

            return compiled_graph

        except Exception as e:
            logger.error(
                "Failed to create DeepAgent",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
