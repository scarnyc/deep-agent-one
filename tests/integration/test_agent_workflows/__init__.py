"""Integration tests for agent workflow orchestration.

This module tests the AgentService layer, which orchestrates agent creation,
invocation, and lifecycle management. Tests verify interactions between:
- AgentService (service layer)
- create_agent (agent factory)
- LangGraph compiled agents

Components Tested:
    - Agent initialization (lazy loading)
    - Agent invocation (message handling)
    - Agent streaming (event generation)
    - Input validation (message/thread_id checks)
    - Error propagation (creation/execution failures)
    - Concurrency (thread-safe agent creation)
    - Sub-agent support (Phase 1 feature)

Mocking Strategy:
    - Mock LangGraph CompiledStateGraph
    - Mock create_agent factory function
    - Mock Settings configuration
    - Real input validation logic

Test Coverage:
    - Service creation and lifecycle
    - Agent invocation patterns
    - Streaming event generation
    - Input validation edge cases
    - Error handling scenarios
    - Concurrent access patterns
"""
