"""
FastAPI dependencies for dependency injection.

Provides reusable dependency functions for endpoints to enable
proper testing with dependency overrides and maintain separation of concerns.
"""
from typing import Annotated

from fastapi import Depends

from backend.deep_agent.services.agent_service import AgentService


def get_agent_service() -> AgentService:
    """
    Dependency that provides an AgentService instance.

    This dependency allows tests to override the service with mocks
    using FastAPI's app.dependency_overrides mechanism.

    Returns:
        AgentService: Initialized agent service instance

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
    """
    return AgentService()


# Type alias for injected AgentService
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
