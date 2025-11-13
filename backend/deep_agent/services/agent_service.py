"""
Agent service for orchestrating agent lifecycle and invocations.

Provides high-level API for creating and interacting with DeepAgents,
managing state persistence, and handling streaming responses.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from langsmith import get_current_run_tree
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from deep_agent.agents.deep_agent import ToolCallLimitedAgent, create_agent
from deep_agent.config.settings import Settings, get_settings
from deep_agent.core.logging import generate_langsmith_url, get_logger

logger = get_logger(__name__)


class AgentService:
    """
    Service for orchestrating agent creation and invocation.

    Provides lazy initialization, state management via checkpointer,
    and streaming support for agent responses.

    Attributes:
        settings: Configuration settings for the agent
        agent: Compiled agent graph (created lazily on first use)
        prompt_variant: Optional prompt variant for A/B testing

    Example:
        >>> service = AgentService()
        >>> result = await service.invoke("Hello", thread_id="user-123")
        >>> print(result["messages"][-1]["content"])

    A/B Testing Example:
        >>> # Test with balanced prompt variant
        >>> service = AgentService(prompt_variant="balanced")
        >>> result = await service.invoke("Hello", thread_id="user-123")
    """

    def __init__(
        self,
        settings: Settings | None = None,
        prompt_variant: str | None = None,
    ):
        """
        Initialize AgentService.

        Args:
            settings: Configuration settings. If None, uses get_settings().
            prompt_variant: Optional prompt variant name for A/B testing.
                           Options: "control", "max_compression", "balanced", "conservative".
                           If None, uses environment-specific prompt (dev/prod).
        """
        self.settings = settings if settings is not None else get_settings()
        self.agent: ToolCallLimitedAgent | None = None
        self.prompt_variant = prompt_variant
        self._agent_lock = asyncio.Lock()  # Thread-safe lazy initialization

        logger.info(
            "AgentService initialized",
            env=self.settings.ENV,
            hitl_enabled=self.settings.ENABLE_HITL,
            subagents_enabled=self.settings.ENABLE_SUB_AGENTS,
            prompt_variant=prompt_variant,
        )

    async def _ensure_agent(self) -> ToolCallLimitedAgent:
        """
        Ensure agent is created (lazy initialization with thread safety).

        Agent instances are created once and reused for all subsequent
        invocations within the same service instance. Uses async lock to
        prevent race conditions during concurrent invocations.

        Returns:
            Tool call limited agent wrapper ready for invocation.

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

            # Create agent with optional prompt variant
            self.agent = await create_agent(
                settings=self.settings,
                subagents=subagents,
                prompt_variant=self.prompt_variant,
            )

            logger.info(
                "Agent created and ready for invocations",
                prompt_variant=self.prompt_variant,
            )

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

            # Capture trace_id from LangSmith for debugging
            trace_id = None
            try:
                run_tree = get_current_run_tree()
                if run_tree:
                    trace_id = str(run_tree.trace_id)
            except Exception:
                # Don't fail if trace_id capture fails
                pass

            logger.info(
                "Agent invocation completed",
                thread_id=thread_id,
                trace_id=trace_id,
                message_count=len(result.get("messages", [])),
            )

            # Add trace_id to result for downstream use
            if trace_id:
                result["trace_id"] = trace_id

            return result

        except Exception as e:
            # Attempt to capture trace_id even on error
            trace_id = None
            try:
                run_tree = get_current_run_tree()
                if run_tree:
                    trace_id = str(run_tree.trace_id)
            except Exception:
                pass

            logger.error(
                "Agent invocation failed",
                thread_id=thread_id,
                trace_id=trace_id,
                langsmith_url=generate_langsmith_url(trace_id) if trace_id else None,
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

        # Diagnostic logging for timeout configuration
        logger.info(
            "Agent streaming timeout configured",
            timeout_seconds=timeout_seconds,
            settings_value=settings.STREAM_TIMEOUT_SECONDS,
            thread_id=thread_id,
        )

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
        trace_id = None

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

                            # Track ALL event types for debugging (not just allowed ones)
                            event_types_seen.add(event_type)

                            # Capture trace_id from first event if not already captured
                            if trace_id is None and event_count == 1:
                                try:
                                    run_tree = get_current_run_tree()
                                    if run_tree:
                                        trace_id = str(run_tree.trace_id)
                                except Exception:
                                    # Don't fail if trace_id capture fails
                                    pass

                            # Filter events based on configuration
                            if event_type in allowed_events:
                                # Add metadata to event
                                if "metadata" not in event:
                                    event["metadata"] = {}
                                event["metadata"]["thread_id"] = thread_id
                                if trace_id:
                                    event["metadata"]["trace_id"] = trace_id

                                # Log progress periodically
                                if event_count % 10 == 0:
                                    logger.debug(
                                        f"Stream event #{event_count}",
                                        thread_id=thread_id,
                                        trace_id=trace_id,
                                        event_type=event_type,
                                    )

                                yield event
                            else:
                                # Log filtered events for debugging (first 50 only to avoid log spam)
                                if event_count <= 50:
                                    logger.debug(
                                        "Filtered event (not in allowed_events)",
                                        thread_id=thread_id,
                                        trace_id=trace_id,
                                        event_type=event_type,
                                        event_name=event.get("name"),
                                        allowed_events=list(allowed_events),
                                    )

            logger.info(
                "Agent streaming completed naturally",
                thread_id=thread_id,
                trace_id=trace_id,
                total_events=event_count,
                event_types=list(event_types_seen),
            )

        except TimeoutError:
            logger.error(
                "Agent streaming timed out",
                thread_id=thread_id,
                trace_id=trace_id,
                langsmith_url=generate_langsmith_url(trace_id) if trace_id else None,
                timeout_seconds=timeout_seconds,
                events_received=event_count,
                event_types=list(event_types_seen),
            )
            # Yield error event to client
            # NOTE: We return here instead of raising to prevent double error events
            # Raising would cause WebSocket handler to send another error event
            yield {
                "event": "on_error",
                "data": {
                    "error": "Agent streaming timed out",
                    "timeout_seconds": timeout_seconds,
                    "events_received": event_count,
                },
                "metadata": {
                    "thread_id": thread_id,
                    "trace_id": trace_id,
                },
            }
            # Return gracefully to prevent double error events
            return

        except asyncio.CancelledError:
            # Determine cancellation source for better diagnostics
            cancellation_reason = "unknown"
            if event_count == 0:
                cancellation_reason = "early_cancellation_before_first_event"
            elif event_count < 10:
                cancellation_reason = "early_cancellation_during_startup"
            else:
                cancellation_reason = "mid_stream_cancellation"

            # Handle cancellation gracefully (client disconnect, task cancelled, etc.)
            logger.warning(
                "Agent streaming cancelled",
                thread_id=thread_id,
                trace_id=trace_id,
                langsmith_url=generate_langsmith_url(trace_id) if trace_id else None,
                events_received=event_count,
                event_types=list(event_types_seen),
                reason=cancellation_reason,
                last_event_type=list(event_types_seen)[-1] if event_types_seen else None,
            )

            # Yield cancellation event to client (if connection still alive)
            try:
                yield {
                    "event": "on_error",
                    "data": {
                        "error": "Agent execution was cancelled",
                        "reason": cancellation_reason,
                        "events_received": event_count,
                        "last_event": list(event_types_seen)[-1] if event_types_seen else None,
                    },
                    "metadata": {
                        "thread_id": thread_id,
                        "trace_id": trace_id,
                    },
                }
            except Exception as e:
                # Connection likely closed, log and continue
                logger.debug(
                    "Failed to send cancellation event (connection closed)",
                    thread_id=thread_id,
                    error=str(e),
                )

            # Do NOT re-raise - cancellation is expected behavior
            return

        except Exception as e:
            logger.error(
                "Agent streaming failed",
                thread_id=thread_id,
                trace_id=trace_id,
                langsmith_url=generate_langsmith_url(trace_id) if trace_id else None,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def get_state(
        self,
        thread_id: str,
        checkpoint_id: str | None = None,
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
        as_node: str | None = None,
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
