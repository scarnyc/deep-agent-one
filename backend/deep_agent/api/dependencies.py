"""
FastAPI dependencies for dependency injection.

Provides reusable dependency functions for endpoints to enable
proper testing with dependency overrides and maintain separation of concerns.
"""
from typing import Annotated

from fastapi import Depends

from deep_agent.services.agent_service import AgentService

# Module-level singleton for AgentService
# Phase 0: Cache service instance to prevent creating expensive service per connection
# Each AgentService initialization creates LangGraph agents, checkpointers, etc.
# WARNING: This makes the service stateful. Must ensure thread safety in Phase 1.
_agent_service_instance: AgentService | None = None


def get_agent_service() -> AgentService:
    """
    Dependency that provides a singleton AgentService instance.

    This dependency allows tests to override the service with mocks
    using FastAPI's app.dependency_overrides mechanism.

    The service is cached as a module-level singleton to avoid expensive
    re-initialization on every request (especially WebSocket connections).

    Returns:
        AgentService: Cached singleton agent service instance

    Example:
        ```python
        @app.get("/example")
        async def example(service: Annotated[AgentService, Depends(get_agent_service)]):
            result = await service.process(...)
            return result
        ```

        # In tests:
        ```python
        app.dependency_overrides[get_agent_service] = lambda: mock_service
        ```

    Note:
        Phase 0: Simple singleton caching
        Phase 1: Consider thread safety, connection pooling, or per-user instances
    """
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance


# Type alias for injected AgentService
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
