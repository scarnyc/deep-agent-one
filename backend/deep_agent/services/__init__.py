"""
Services layer for Deep Agent AGI.

This module provides the business logic layer that orchestrates agent operations,
state management, and coordinates between the API layer and agent implementations.

Key Components:
    - AgentService: Main orchestration service for agent lifecycle and invocations
    - LLM Factory: Factory functions for creating LangChain-compatible LLM instances

Architecture:
    The services layer implements a three-tier architecture:

    API Layer (FastAPI endpoints)
        |
        v
    Services Layer (business logic, orchestration)
        |
        v
    Agents Layer (LangGraph DeepAgents, tools, integrations)

Design Patterns:
    - Lazy Initialization: Agents created on first use for performance
    - State Management: LangGraph checkpointer for conversation persistence
    - Streaming Support: AsyncGenerator for real-time responses via astream_events()
    - Retry Logic: Exponential backoff for transient failures
    - Thread Safety: Async locks for concurrent agent creation

Example Usage:
    >>> from deep_agent.services.agent_service import AgentService
    >>>
    >>> # Create service instance
    >>> service = AgentService()
    >>>
    >>> # Invoke agent (non-streaming)
    >>> result = await service.invoke(
    ...     message="What files are in the current directory?",
    ...     thread_id="user-123"
    ... )
    >>> print(result["messages"][-1]["content"])
    >>>
    >>> # Stream agent response (streaming)
    >>> async for event in service.stream("Hello", "user-456"):
    ...     if event["event"] == "on_chat_model_stream":
    ...         chunk = event["data"]["chunk"]
    ...         if hasattr(chunk, "content"):
    ...             print(chunk.content, end="")

See Also:
    - ../agents/: Agent implementations and tools
    - ../api/: FastAPI endpoints that use these services
    - ../integrations/: External service integrations (LangSmith, Perplexity)
    - ../models/: Data models and GPT-5 configuration
"""
