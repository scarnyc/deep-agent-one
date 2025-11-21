"""Integration tests for Deep Agent AGI.

This package contains integration tests that verify interactions between
multiple components of the system. Integration tests use mocked external
services (OpenAI, Perplexity MCP) but test realistic workflows across
internal architectural boundaries.

Modules:
    test_agent_workflows: Tests for agent service orchestration
    test_api_endpoints: Tests for FastAPI endpoints (chat, WebSocket, agents)
    test_mcp_integration: Tests for MCP client integrations
    test_tool_event_streaming: Tests for event streaming through agent service
    test_websocket_cancellation: Tests for WebSocket cancellation handling

Test Philosophy:
    - Focus on component interactions, not isolated units
    - Mock external dependencies (APIs, MCP servers)
    - Test realistic user workflows end-to-end
    - Verify error propagation across boundaries
    - Use real database operations where appropriate

Coverage Expectations:
    - Integration tests complement unit tests
    - Target: 80%+ combined coverage
    - Focus on happy paths + critical error scenarios
    - Verify contracts between layers

Running Integration Tests:
    # All integration tests
    pytest tests/integration/ -v

    # Specific test suite
    pytest tests/integration/test_api_endpoints/ -v

    # With coverage
    pytest tests/integration/ --cov=backend.deep_agent --cov-report=html
"""
