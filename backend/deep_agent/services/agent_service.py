"""
Agent service for orchestrating agent lifecycle and invocations.

Provides high-level API for creating and interacting with DeepAgents,
managing state persistence, and handling streaming responses.
"""

import asyncio
from typing import Any, AsyncGenerator, Optional

from langgraph.graph.state import CompiledStateGraph
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

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

        # Invoke agent with retry logic for transient failures
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
                reraise=True,
            ):
                with attempt:
                    if attempt.retry_state.attempt_number > 1:
                        logger.warning(
                            "Retrying agent invocation",
                            thread_id=thread_id,
                            attempt=attempt.retry_state.attempt_number,
                        )

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
        Stream agent response events for real-time updates using astream_events() API.

        This method uses LangGraph's astream_events() API which provides fine-grained
        event streaming including:
        - on_chat_model_stream: Individual LLM token streaming
        - on_tool_start/on_tool_end: Tool execution lifecycle
        - on_chain_start/on_chain_end: Agent/chain execution lifecycle

        Args:
            message: User message to send to the agent.
            thread_id: Thread ID for conversation state persistence.

        Yields:
            Event dictionaries containing streaming updates in LangGraph v2 format.

        Raises:
            ValueError: If message is empty or thread_id is invalid.
            RuntimeError: If agent execution fails.

        Example:
            >>> async for event in service.stream("Hello", "user-789"):
            ...     if event["event"] == "on_chat_model_stream":
            ...         chunk = event["data"]["chunk"]
            ...         if hasattr(chunk, "content"):
            ...             print(chunk.content, end="")
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

        # Prepare config (no stream_mode needed for astream_events)
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Get streaming configuration from settings
        settings = get_settings()
        allowed_events = set(settings.stream_allowed_events_list)
        timeout_seconds = settings.STREAM_TIMEOUT_SECONDS
        stream_version = settings.STREAM_VERSION

        # Stream events with retry logic for initial connection
        logger.info(
            "Starting agent streaming with astream_events()",
            thread_id=thread_id,
            message_preview=message[:50] if len(message) > 50 else message,
            stream_version=stream_version,
            allowed_events=list(allowed_events),
        )

        event_count = 0
        event_types_seen = set()

        try:
            # Wrap streaming in timeout to prevent infinite hangs
            async with asyncio.timeout(timeout_seconds):
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
                    reraise=True,
                ):
                    with attempt:
                        if attempt.retry_state.attempt_number > 1:
                            logger.warning(
                                "Retrying agent streaming",
                                thread_id=thread_id,
                                attempt=attempt.retry_state.attempt_number,
                            )

                        # Use astream_events() for fine-grained event streaming
                        # This provides real-time token streaming and tool execution events
                        async for event in agent.astream_events(input_data, config, version=stream_version):
                            event_count += 1
                            event_type = event.get("event", "unknown")

                            # Filter events based on configuration
                            if event_type in allowed_events:
                                event_types_seen.add(event_type)

                                # Add metadata to event
                                if "metadata" not in event:
                                    event["metadata"] = {}
                                event["metadata"]["thread_id"] = thread_id

                                # Log progress periodically
                                if event_count % 10 == 0:
                                    logger.debug(
                                        f"Stream event #{event_count}",
                                        thread_id=thread_id,
                                        event_type=event_type,
                                    )

                                yield event

            logger.info(
                "Agent streaming completed naturally",
                thread_id=thread_id,
                total_events=event_count,
                event_types=list(event_types_seen),
            )

        except asyncio.TimeoutError:
            logger.error(
                "Agent streaming timed out",
                thread_id=thread_id,
                timeout_seconds=timeout_seconds,
                events_received=event_count,
                event_types=list(event_types_seen),
            )
            # Yield error event to client before raising
            yield {
                "event": "on_error",
                "data": {
                    "error": "Agent streaming timed out",
                    "timeout_seconds": timeout_seconds,
                    "events_received": event_count,
                },
            }
            raise RuntimeError(f"Agent streaming timed out after {timeout_seconds}s")

        except Exception as e:
            logger.error(
                "Agent streaming failed",
                thread_id=thread_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def get_state(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get current state from checkpointer for a thread.

        Retrieves the persisted state for a conversation thread,
        including messages, agent status, and execution metadata.

        Args:
            thread_id: Thread ID to get state for.
            checkpoint_id: Optional specific checkpoint ID. If None, gets latest.

        Returns:
            State dictionary containing:
                - values: Current state values (messages, etc.)
                - next: List of next nodes to execute (empty if completed)
                - config: Configuration including thread_id and checkpoint_id
                - metadata: State metadata
                - created_at: When the state was created
                - parent_config: Parent checkpoint config (if any)

        Raises:
            ValueError: If thread_id is empty or thread not found.
            RuntimeError: If state retrieval fails.

        Example:
            >>> state = await service.get_state("user-123")
            >>> print(state["values"]["messages"])
            >>> print("Running" if state["next"] else "Completed")
        """
        if not thread_id or not thread_id.strip():
            raise ValueError("Thread ID cannot be empty")

        logger.debug(
            "Getting agent state",
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
        )

        # Ensure agent is created
        agent = await self._ensure_agent()

        # Prepare config
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id

        # Get state from checkpointer
        try:
            state = await agent.aget_state(config)

            if state is None:
                raise ValueError(f"Thread not found: {thread_id}")

            logger.debug(
                "Agent state retrieved",
                thread_id=thread_id,
                has_next=len(state.next) > 0,
            )

            # Convert StateSnapshot to dict for API response
            return {
                "values": state.values,
                "next": list(state.next),
                "config": state.config,
                "metadata": state.metadata,
                "created_at": state.created_at,
                "parent_config": state.parent_config,
            }

        except ValueError:
            # Re-raise ValueError (thread not found)
            raise

        except Exception as e:
            logger.error(
                "Failed to get agent state",
                thread_id=thread_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise RuntimeError(f"Failed to get state: {str(e)}") from e

    async def update_state(
        self,
        thread_id: str,
        values: dict[str, Any],
        as_node: Optional[str] = None,
    ) -> None:
        """
        Update state in checkpointer (for HITL approval).

        Updates the persisted state for a conversation thread,
        typically used to provide human feedback or approval for
        agent actions (HITL workflow).

        Args:
            thread_id: Thread ID to update state for.
            values: State values to update (e.g., approval decision).
            as_node: Optional node name to attribute update to.

        Raises:
            ValueError: If thread_id is empty or thread not found.
            RuntimeError: If state update fails.

        Example:
            >>> # Approve HITL request
            >>> await service.update_state(
            ...     thread_id="user-123",
            ...     values={"approved": True},
            ...     as_node="human"
            ... )
        """
        if not thread_id or not thread_id.strip():
            raise ValueError("Thread ID cannot be empty")

        logger.info(
            "Updating agent state",
            thread_id=thread_id,
            as_node=as_node,
            update_keys=list(values.keys()),
        )

        # Ensure agent is created
        agent = await self._ensure_agent()

        # Prepare config
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        # Update state
        try:
            await agent.aupdate_state(config, values, as_node=as_node)

            logger.info(
                "Agent state updated successfully",
                thread_id=thread_id,
            )

        except Exception as e:
            logger.error(
                "Failed to update agent state",
                thread_id=thread_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise RuntimeError(f"Failed to update state: {str(e)}") from e
