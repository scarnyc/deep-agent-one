"""
FastAPI dependencies for dependency injection.

Provides reusable dependency functions for endpoints to enable
proper testing with dependency overrides and maintain separation of concerns.

Thread Safety
-------------
This module implements thread-safe singleton management for AgentService using:
- Double-checked locking pattern in get_agent_service()
- threading.Lock for synchronization (appropriate for sync FastAPI dependencies)

The implementation ensures that:
1. Only one AgentService instance is created even under concurrent access
2. reset_agent_service() safely invalidates the cache
3. All operations are atomic with respect to the global state

Note: threading.Lock is used instead of asyncio.Lock because FastAPI runs
synchronous dependencies in a thread pool, making threading primitives appropriate.
"""

import threading
from typing import Annotated

from fastapi import Depends

from deep_agent.core.logging import get_logger
from deep_agent.services.agent_service import AgentService

logger = get_logger(__name__)


class AgentServiceInitializationError(RuntimeError):
    """Raised when AgentService fails to initialize."""


# Module-level singleton for AgentService (thread-safe with double-checked locking)
# Cache service instance to prevent creating expensive service per connection
# Each AgentService initialization creates LangGraph agents, checkpointers, etc.
_agent_service_instance: AgentService | None = None
_agent_service_lock: threading.Lock = threading.Lock()
_agent_service_version: int = 0
# Monotonic creation counter for debugging concurrent access patterns.
# Incremented on each successful AgentService() creation and NOT reset
# by reset_agent_service().


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
        Thread-safe singleton with double-checked locking pattern.
        The lock ensures only one thread creates the instance even under
        concurrent access. See module docstring for thread safety details.
    """
    global _agent_service_instance, _agent_service_version
    if _agent_service_instance is None:
        with _agent_service_lock:
            # Double-checked locking to prevent race condition under concurrent requests
            if _agent_service_instance is None:
                try:
                    logger.debug(
                        "Creating new AgentService instance",
                        version=_agent_service_version + 1,
                    )
                    _agent_service_instance = AgentService()
                    _agent_service_version += 1
                    logger.info(
                        "AgentService instance created successfully",
                        version=_agent_service_version,
                    )
                # Intentionally catch all exceptions to wrap them in a domain-specific
                # initialization error for FastAPI consumers. AgentService init can fail
                # for many reasons (config, network, dependencies) that we want to handle
                # uniformly at the API layer.
                except Exception as e:  # noqa: BLE001
                    logger.error(
                        "Failed to initialize AgentService",
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise AgentServiceInitializationError(
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

    Thread Safety:
        This function acquires _agent_service_lock before modifying the
        global state, ensuring atomic updates even under concurrent access.
        The lock prevents race conditions where multiple threads might
        attempt to reset simultaneously.

    Note:
        The version counter (_agent_service_version) is NOT reset by this
        function. It tracks total instance creations across the process
        lifetime for debugging purposes:
            Create → version = 1
            Reset  → version stays 1 (instance cleared, counter unchanged)
            Create → version = 2

    Example:
        >>> from deep_agent.api.dependencies import reset_agent_service
        >>> from deep_agent.config.settings import clear_settings_cache
        >>> # After changing ENV in .env file:
        >>> clear_settings_cache()
        >>> reset_agent_service()
        >>> # Next request will use new settings
    """
    global _agent_service_instance
    with _agent_service_lock:
        if _agent_service_instance is not None:
            logger.debug(
                "Resetting AgentService instance",
                current_version=_agent_service_version,
            )
        _agent_service_instance = None


# Type alias for injected AgentService
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]


def get_agent_service_version() -> int:
    """Get the current AgentService creation count (thread-safe read).

    Returns the number of times an AgentService instance has been successfully
    created in this process. The counter is monotonic and is NOT reset by
    :func:`reset_agent_service`. Useful for debugging concurrent access patterns.

    Thread Safety:
        Acquires the lock to ensure consistent read of shared mutable state,
        following the principle that all accesses to shared state should be
        protected by the same lock.

    Returns:
        int: Current creation count (0 if never created).
    """
    with _agent_service_lock:
        return _agent_service_version


# Explicit public API for IDE autocomplete and import hygiene
# Note: _agent_service_lock is intentionally NOT in __all__ as it's a private
# implementation detail. Tests can still access it via direct import.
__all__ = [
    "AgentServiceInitializationError",
    "get_agent_service",
    "AgentServiceDep",
    "reset_agent_service",
    "get_agent_service_version",
]
