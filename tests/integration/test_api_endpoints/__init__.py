"""Integration tests for FastAPI endpoints.

This module tests the API layer endpoints, verifying request/response handling,
validation, error propagation, and protocol compliance. Tests cover:
- RESTful chat endpoints (/api/v1/chat)
- Server-Sent Events streaming (/api/v1/chat/stream)
- WebSocket real-time communication (/api/v1/ws)
- Agent management endpoints (/api/v1/agents)

Endpoints Tested:
    - POST /api/v1/chat - Synchronous chat
    - POST /api/v1/chat/stream - SSE streaming chat
    - WebSocket /api/v1/ws - Bidirectional agent communication
    - GET /api/v1/agents/{thread_id} - Agent status
    - POST /api/v1/agents/{thread_id}/approve - HITL approval

Components Tested:
    - Request validation (Pydantic models)
    - Response formatting (ChatResponse, SSE, WebSocket)
    - Rate limiting (slowapi)
    - CORS headers
    - Error handling (4xx, 5xx)
    - Request ID tracking

Mocking Strategy:
    - Mock AgentService for agent execution
    - Real FastAPI TestClient
    - Real request validation
    - Real middleware (CORS, rate limiting)

Test Scenarios:
    - Valid requests (happy path)
    - Invalid input (validation errors)
    - Agent errors (5xx handling)
    - Streaming events (SSE, WebSocket)
    - Concurrent requests
    - Rate limit enforcement
"""
