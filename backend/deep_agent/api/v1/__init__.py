"""
API Version 1 Routes.

This module registers all v1 API routers for the Deep Agent AGI application.
Includes RESTful endpoints for chat, agent management, configuration, and HITL workflows.

Routers:
    - chat: Chat endpoints (POST /chat, POST /chat/stream)
    - agents: Agent management and HITL approval endpoints
    - config: Public configuration endpoint (GET /config/public)

Usage:
    from deep_agent.api.v1 import agents, chat, config
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
    app.include_router(config.router, prefix="/api/v1", tags=["config"])
"""
