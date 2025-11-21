"""
API Version 1 Routes.

This module registers all v1 API routers for the Deep Agent AGI application.
Includes RESTful endpoints for chat, agent management, and HITL workflows.

Routers:
    - chat: Chat endpoints (POST /chat, POST /chat/stream)
    - agents: Agent management and HITL approval endpoints

Usage:
    from deep_agent.api.v1 import agents, chat
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
"""
