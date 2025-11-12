"""
API package for Deep Agent AGI backend.

This package contains the FastAPI application setup and all HTTP/WebSocket
endpoints for the Deep Agent AGI system. The API follows versioning best
practices with v1 endpoints under `/api/v1/`.

Modules:
    dependencies: Dependency injection for FastAPI endpoints
    middleware: Custom middleware for timeout, logging, etc.
    v1: Version 1 API routes (chat, agents, WebSocket)

Example:
    ```python
    from deep_agent.api.dependencies import get_agent_service
    from fastapi import Depends

    @app.get("/example")
    async def example(service = Depends(get_agent_service)):
        return await service.invoke(...)
    ```
"""
