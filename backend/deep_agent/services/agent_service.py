"""
Agent service for orchestrating agent lifecycle and invocations.

Provides high-level API for creating and interacting with DeepAgents,
managing state persistence, and handling streaming responses.
"""

import asyncio
from typing import Any, AsyncGenerator, Optional

from langgraph.graph.state import CompiledStateGraph

from backend.deep_agent.agents.deep_agent import create_agent
from backend.deep_agent.config.settings import Settings, get_settings
from backend.deep_agent.core.logging import get_logger

logger = get_logger(__name__)


class AgentService:
    """
    Service for orchestrating agent creation and invocation.

    Provides lazy initialization, state management via checkpointer,
    and streaming support for agent responses.

    Attributes:
        settings: Configuration settings for the agent
        agent: Compiled agent graph (created lazily on first use)

    Example:
        >>> service = AgentService()
        >>> result = await service.invoke("Hello", thread_id="user-123")
        >>> print(result["messages"][-1]["content"])
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize AgentService.

        Args:
            settings: Configuration settings. If None, uses get_settings().
        """
        self.settings = settings if settings is not None else get_settings()
        self.agent: Optional[CompiledStateGraph] = None
        self._agent_lock = asyncio.Lock()  # Thread-safe lazy initialization

        logger.info(
            "AgentService initialized",
            env=self.settings.ENV,
            hitl_enabled=self.settings.ENABLE_HITL,
            subagents_enabled=self.settings.ENABLE_SUB_AGENTS,
        )

    async def _ensure_agent(self) -> CompiledStateGraph:
        """
        Ensure agent is created (lazy initialization with thread safety).

        Agent instances are created once and reused for all subsequent
        invocations within the same service instance. Uses async lock to
        prevent race conditions during concurrent invocations.

        Returns:
            Compiled agent graph ready for invocation.

        Raises:
            ValueError: If agent creation fails due to invalid configuration.
            RuntimeError: If agent compilation fails.
        """
        # Fast path: check without lock first
        if self.agent is not None:
            return self.agent

        # Acquire lock for agent creation
        async with self._agent_lock:
            # Double-check after acquiring lock (another task may have created it)
            if self.agent is not None:
                return self.agent

            logger.debug("Creating agent (lazy initialization)")

            # Determine subagents parameter
            subagents = None
            if self.settings.ENABLE_SUB_AGENTS:
                # Phase 0: empty list (no custom subagents yet)
                # Phase 1+: would load custom subagents here
                subagents = None  # DeepAgents handles default general-purpose subagent

            # Create agent
            self.agent = await create_agent(
                settings=self.settings,
                subagents=subagents,
            )

            logger.info("Agent created and ready for invocations")

        return self.agent

    async def invoke(
        self,
        message: str,
        thread_id: str,
    ) -> dict[str, Any]:
        """
        Invoke agent with a message and return complete response.

        Args:
            message: User message to send to the agent.
            thread_id: Thread ID for conversation state persistence.

        Returns:
            Agent response containing messages and state.

        Raises:
            ValueError: If message is empty or thread_id is invalid.
            RuntimeError: If agent execution fails.

        Example:
            >>> result = await service.invoke(
            ...     message="What files are in the current directory?",
            ...     thread_id="user-456"
            ... )
            >>> assistant_message = result["messages"][-1]["content"]
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        if not thread_id or not thread_id.strip():
            raise ValueError("Thread ID cannot be empty")

        logger.info(
            "Invoking agent",
            thread_id=thread_id,
            message_length=len(message),
        )

        # Ensure agent is created
        agent = await self._ensure_agent()

        # Prepare input
        input_data = {
            "messages": [
                {"role": "user", "content": message}
            ]
        }

        # Prepare config with thread_id for checkpointer
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Invoke agent
        try:
            result = await agent.ainvoke(input_data, config)

            logger.info(
                "Agent invocation completed",
                thread_id=thread_id,
                message_count=len(result.get("messages", [])),
            )

            return result

        except Exception as e:
            logger.error(
                "Agent invocation failed",
                thread_id=thread_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def stream(
        self,
        message: str,
        thread_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream agent response events for real-time updates.

        Args:
            message: User message to send to the agent.
            thread_id: Thread ID for conversation state persistence.

        Yields:
            Event dictionaries containing streaming updates.

        Raises:
            ValueError: If message is empty or thread_id is invalid.
            RuntimeError: If agent execution fails.

        Example:
            >>> async for event in service.stream("Hello", "user-789"):
            ...     if event["event"] == "on_chat_model_stream":
            ...         print(event["data"]["chunk"]["content"], end="")
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        if not thread_id or not thread_id.strip():
            raise ValueError("Thread ID cannot be empty")

        logger.info(
            "Streaming agent response",
            thread_id=thread_id,
            message_length=len(message),
        )

        # Ensure agent is created
        agent = await self._ensure_agent()

        # Prepare input
        input_data = {
            "messages": [
                {"role": "user", "content": message}
            ]
        }

        # Prepare config
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Stream events
        try:
            async for event in agent.astream_events(input_data, config, version="v2"):
                yield event

            logger.info(
                "Agent streaming completed",
                thread_id=thread_id,
            )

        except Exception as e:
            logger.error(
                "Agent streaming failed",
                thread_id=thread_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
