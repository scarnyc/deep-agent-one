"""
FastAPI dependencies for dependency injection.

Provides reusable dependency functions for endpoints to enable
proper testing with dependency overrides and maintain separation of concerns.
"""
from typing import Annotated

from fastapi import Depends

from deep_agent.core.logging import get_logger
from deep_agent.services.agent_service import AgentService

logger = get_logger(__name__)

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
        try:
            _agent_service_instance = AgentService()
        except Exception as e:
            logger.error(
                "Failed to initialize AgentService",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise RuntimeError(
                "Agent service initialization failed. Check configuration."
            ) from e
    return _agent_service_instance


def reset_agent_service() -> None:
    """Reset the singleton AgentService instance.

    Call this function to invalidate the cached AgentService instance,
    forcing the next call to get_agent_service() to create a new instance.
    This is useful when settings have changed and the agent needs to be
    recreated with new configuration (e.g., different ENV/prompt mode).

    Should be called in conjunction with clear_settings_cache() to ensure
    both settings and agent service are refreshed.

    Example:
        >>> from deep_agent.api.dependencies import reset_agent_service
        >>> from deep_agent.config.settings import clear_settings_cache
        >>> # After changing ENV in .env file:
        >>> clear_settings_cache()
        >>> reset_agent_service()
        >>> # Next request will use new settings
    """
    global _agent_service_instance
    _agent_service_instance = None


# Type alias for injected AgentService
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]

# Explicit public API for IDE autocomplete and import hygiene
__all__ = ["get_agent_service", "AgentServiceDep", "reset_agent_service"]
