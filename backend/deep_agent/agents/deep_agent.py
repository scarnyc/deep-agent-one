"""DeepAgent creation and configuration using LangChain's create_deep_agent API."""

import traceback
from collections.abc import AsyncIterator
from typing import Any

from deepagents import create_deep_agent
from langgraph.graph.state import CompiledStateGraph

from deep_agent.agents.checkpointer import CheckpointerManager
from deep_agent.agents.prompts import get_agent_instructions
from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.logging import get_logger
from deep_agent.integrations.langsmith import setup_langsmith
from deep_agent.models.gpt5 import GPT5Config, ReasoningEffort, Verbosity
from deep_agent.services.llm_factory import create_gpt5_llm
from deep_agent.tools.web_search import web_search

logger = get_logger(__name__)


class ToolCallLimitedAgent:
    """
    Wrapper for CompiledStateGraph that enforces tool call limits per invocation.

    This wrapper intercepts tool execution events and maintains a count of tool
    calls. When the limit is reached, it allows the current tool call to complete,
    then gracefully terminates the agent, allowing it to emit a final response.

    Attributes:
        graph: The underlying CompiledStateGraph to wrap
        max_tool_calls: Maximum number of tool calls per invocation
        _tool_call_count: Current count of tool calls (reset per invocation)
        _limit_reached: Flag indicating if limit has been reached
    """

    def __init__(self, graph: CompiledStateGraph, max_tool_calls: int = 10):
        """
        Initialize the tool call limited agent wrapper.

        Args:
            graph: CompiledStateGraph to wrap
            max_tool_calls: Maximum tool calls per invocation (default: 10)
        """
        self.graph = graph
        self.max_tool_calls = max_tool_calls
        self._tool_call_count = 0
        self._limit_reached = False

    def _reset_counter(self) -> None:
        """Reset tool call counter for new invocation."""
        self._tool_call_count = 0
        self._limit_reached = False

    def _should_terminate(self) -> bool:
        """Check if agent should terminate due to tool call limit."""
        return self._limit_reached

    async def astream(
        self, input: dict[str, Any], config: dict[str, Any] | None = None
    ) -> AsyncIterator[Any]:
        """
        Stream agent execution with tool call limit enforcement.

        Args:
            input: Input message/state for the agent
            config: Configuration dictionary with thread_id, etc.

        Yields:
            Stream events from the underlying agent

        Note:
            Tool calls are counted by monitoring on_tool_* events.
            After the 10th tool call completes, the agent continues to synthesize
            results. If the agent attempts an 11th tool call, it is blocked and
            the agent terminates gracefully.
        """
        self._reset_counter()

        async for event in self.graph.astream(input, config):
            # Track tool calls via event monitoring
            # LangGraph emits various events - we count tool executions
            if isinstance(event, dict):
                # Check for tool execution events (LangGraph v1 and v2 patterns)
                event_name = event.get("event")
                if event_name in ["on_tool_start", "on_tool_call_start"]:
                    # Check if we're already at limit BEFORE allowing new tool
                    if self._tool_call_count >= self.max_tool_calls:
                        # Agent is attempting 11th+ tool call - block it
                        logger.warning(
                            "Blocking tool call beyond limit - agent should synthesize",
                            attempted_call=self._tool_call_count + 1,
                            limit=self.max_tool_calls,
                        )

                        # Add metadata to LangSmith trace for observability
                        try:
                            # Lazy import to avoid blocking module load during test collection
                            from langsmith import get_current_run_tree

                            run_tree = get_current_run_tree()
                            if run_tree:
                                run_tree.add_metadata({
                                    "tool_limit_exceeded": True,
                                    "blocked_tool_call": self._tool_call_count + 1,
                                    "max_tool_calls": self.max_tool_calls,
                                })
                                logger.debug("Added tool limit block metadata to LangSmith trace")
                        except Exception as e:
                            # Don't fail if LangSmith tracing is unavailable
                            logger.debug(f"Could not add LangSmith metadata: {e}")

                        # Emit termination event - agent exceeded limit
                        yield {
                            "event": "on_chain_end",
                            "data": {
                                "output": {
                                    "status": "completed",
                                    "reason": "tool_call_limit_exceeded",
                                    "tool_calls": self._tool_call_count,
                                }
                            },
                        }
                        # Stop iteration - no more events
                        break

                    # Increment counter for this tool call
                    self._tool_call_count += 1
                    logger.debug(
                        "Tool call tracked",
                        count=self._tool_call_count,
                        limit=self.max_tool_calls,
                    )

                    # If this is the 10th tool, mark limit reached but continue
                    if self._tool_call_count == self.max_tool_calls:
                        self._limit_reached = True
                        logger.info(
                            "Tool call limit reached - allowing synthesis after this tool",
                            count=self._tool_call_count,
                            limit=self.max_tool_calls,
                        )

                        # Add metadata to LangSmith trace for observability
                        try:
                            # Lazy import to avoid blocking module load during test collection
                            from langsmith import get_current_run_tree

                            run_tree = get_current_run_tree()
                            if run_tree:
                                run_tree.add_metadata({
                                    "tool_limit_reached": True,
                                    "tool_call_count": self._tool_call_count,
                                    "max_tool_calls": self.max_tool_calls,
                                })
                                logger.debug("Added tool limit metadata to LangSmith trace")
                        except Exception as e:
                            # Don't fail if LangSmith tracing is unavailable
                            logger.debug(f"Could not add LangSmith metadata: {e}")

            # Yield event to caller (including 10th tool events)
            yield event

            # Note: We do NOT terminate here after the 10th tool completes.
            # The agent needs to continue to synthesize results and generate
            # a response. We only block and terminate if the agent tries to
            # make an 11th tool call (handled above).

    async def ainvoke(
        self, input: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Invoke agent with tool call limit enforcement.

        Args:
            input: Input message/state for the agent
            config: Configuration dictionary with thread_id, etc.

        Returns:
            Final agent state/output

        Note:
            For non-streaming invocations, we wrap the underlying ainvoke
            and monitor via stream events internally.
        """
        self._reset_counter()

        # For ainvoke, we still need to monitor tool calls
        # We'll use astream internally and collect the final result
        final_result = None
        async for event in self.astream(input, config):
            # Collect final result from stream
            if isinstance(event, dict) and event.get("event") == "on_chain_end":
                final_result = event.get("data", {}).get("output", {})

        return final_result or {}

    async def astream_events(
        self,
        input: dict[str, Any],
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[Any]:
        """
        Stream agent events with tool call limit enforcement.

        This method is used by AgentService.stream() for production WebSocket
        streaming. It implements the same tool call limiting logic as astream()
        but for the astream_events() API.

        Args:
            input: Input message/state for the agent
            config: Configuration dictionary with thread_id, etc.
            **kwargs: Additional arguments (version, include_names, etc.)

        Yields:
            Stream events from the underlying agent (LangGraph event format)

        Note:
            Tool calls are counted by monitoring on_tool_* events.
            After the 10th tool call completes, the agent continues to synthesize
            results. If the agent attempts an 11th tool call, it is blocked and
            the agent terminates gracefully.
        """
        self._reset_counter()

        async for event in self.graph.astream_events(input, config, **kwargs):
            # Track tool calls via event monitoring
            # LangGraph emits various events - we count tool executions
            if isinstance(event, dict):
                # Check for tool execution events (LangGraph v1 and v2 patterns)
                event_name = event.get("event")
                if event_name in ["on_tool_start", "on_tool_call_start"]:
                    # Check if we're already at limit BEFORE allowing new tool
                    if self._tool_call_count >= self.max_tool_calls:
                        # Agent is attempting 11th+ tool call - block it
                        logger.warning(
                            "Blocking tool call beyond limit - agent should synthesize",
                            attempted_call=self._tool_call_count + 1,
                            limit=self.max_tool_calls,
                        )

                        # Add metadata to LangSmith trace for observability
                        try:
                            # Lazy import to avoid blocking module load during test collection
                            from langsmith import get_current_run_tree

                            run_tree = get_current_run_tree()
                            if run_tree:
                                run_tree.add_metadata({
                                    "tool_limit_exceeded": True,
                                    "blocked_tool_call": self._tool_call_count + 1,
                                    "max_tool_calls": self.max_tool_calls,
                                })
                                logger.debug("Added tool limit block metadata to LangSmith trace")
                        except Exception as e:
                            # Don't fail if LangSmith tracing is unavailable
                            logger.debug(f"Could not add LangSmith metadata: {e}")

                        # Emit termination event - agent exceeded limit
                        yield {
                            "event": "on_chain_end",
                            "data": {
                                "output": {
                                    "status": "completed",
                                    "reason": "tool_call_limit_exceeded",
                                    "tool_calls": self._tool_call_count,
                                }
                            },
                        }
                        # Stop iteration - no more events
                        break

                    # Increment counter for this tool call
                    self._tool_call_count += 1
                    logger.debug(
                        "Tool call tracked",
                        count=self._tool_call_count,
                        limit=self.max_tool_calls,
                    )

                    # If this is the 10th tool, mark limit reached but continue
                    if self._tool_call_count == self.max_tool_calls:
                        self._limit_reached = True
                        logger.info(
                            "Tool call limit reached - allowing synthesis after this tool",
                            count=self._tool_call_count,
                            limit=self.max_tool_calls,
                        )

                        # Add metadata to LangSmith trace for observability
                        try:
                            # Lazy import to avoid blocking module load during test collection
                            from langsmith import get_current_run_tree

                            run_tree = get_current_run_tree()
                            if run_tree:
                                run_tree.add_metadata({
                                    "tool_limit_reached": True,
                                    "tool_call_count": self._tool_call_count,
                                    "max_tool_calls": self.max_tool_calls,
                                })
                                logger.debug("Added tool limit metadata to LangSmith trace")
                        except Exception as e:
                            # Don't fail if LangSmith tracing is unavailable
                            logger.debug(f"Could not add LangSmith metadata: {e}")

            # Yield event to caller (including 10th tool events)
            yield event

            # Note: We do NOT terminate here after the 10th tool completes.
            # The agent needs to continue to synthesize results and generate
            # a response. We only block and terminate if the agent tries to
            # make an 11th tool call (handled above).

    def __getattr__(self, name: str) -> Any:
        """
        Delegate attribute access to underlying graph for compatibility.

        This allows the wrapper to act as a drop-in replacement for
        CompiledStateGraph, forwarding any methods/attributes we don't
        explicitly override.
        """
        return getattr(self.graph, name)


async def create_agent(
    settings: Settings | None = None,
    subagents: list[Any] | None = None,
    prompt_variant: str | None = None,
) -> ToolCallLimitedAgent:
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
        ToolCallLimitedAgent wrapping CompiledStateGraph with tool call limit
        enforcement, ready for invocation with checkpointer attached

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

    # Create DeepAgent using official API
    try:
        logger.debug(
            "Calling create_deep_agent with parameters",
            model_type=type(llm).__name__,
            tools_count=1,  # [web_search]
            system_prompt_length=len(system_prompt) if system_prompt else 0,
            subagents=subagents,
            has_checkpointer=checkpointer is not None,
        )

        compiled_graph = create_deep_agent(
            model=llm,
            tools=[web_search],  # Custom tools in addition to built-in tools
            system_prompt=system_prompt,  # DeepAgents 0.2.0: parameter renamed from 'instructions'
            subagents=subagents,
            checkpointer=checkpointer,
        )

        # Wrap with tool call limiter for graceful termination
        max_tool_calls = settings.MAX_TOOL_CALLS_PER_INVOCATION
        limited_agent = ToolCallLimitedAgent(
            graph=compiled_graph,
            max_tool_calls=max_tool_calls,
        )

        logger.info(
            "Successfully created and compiled DeepAgent with tool call limit",
            has_checkpointer=checkpointer is not None,
            subagents_enabled=subagents is not None and len(subagents) > 0,
            max_tool_calls=max_tool_calls,
        )

        return limited_agent

    except Exception as e:
        # Log full traceback for debugging
        logger.error(
            "Failed to create DeepAgent",
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc(),
        )
        raise
