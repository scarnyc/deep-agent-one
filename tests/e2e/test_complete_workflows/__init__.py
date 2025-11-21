"""
Complete Workflow Tests for Core System Functionality.

This module contains E2E tests for fundamental workflows that represent the
core functionality of the Deep Agent AGI system. These tests validate complete
end-to-end flows for essential features.

Workflows Covered:
    1. Basic Chat Workflow (test_basic_chat.py)
       - User sends message ’ Agent processes ’ Response returned
       - Conversation history management
       - Input validation and error handling
       - Response time performance

    2. Human-in-the-Loop (HITL) Workflow (test_hitl_workflow.py)
       - Agent requests approval ’ User approves/rejects ’ Agent continues
       - State persistence during interruption
       - Multiple approval checkpoints
       - Timeout handling

    3. Tool Usage Workflow (test_tool_usage.py)
       - Agent invokes file system tools (ls, read_file, write_file, edit_file)
       - Agent uses web search tool (Perplexity MCP)
       - Multiple tools in sequence
       - Tool error handling

Testing Approach:
    - Mock only external APIs (OpenAI, Perplexity, LangSmith)
    - Test complete internal flow (API ’ Service ’ Agent ’ Tools)
    - Verify state persistence through checkpointer
    - Validate response structure and business logic
    - Measure performance against success criteria

Success Criteria (Phase 0):
    - Response latency: <2s for simple queries
    - Tool execution: <2s for file operations
    - HITL approval: <30s user response time (no timeout)
    - API error rate: <1%
    - Thread safety: Concurrent requests isolated

Example:
    ```python
    # Test complete chat workflow
    def test_complete_chat_request_response_cycle(client):
        # Arrange
        request_data = {
            "message": "Hello, how can you help me?",
            "thread_id": "test-thread-001",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    ```

See Also:
    - tests/e2e/test_user_journeys/: Multi-step user scenarios
    - tests/e2e/test_reasoning_scenarios/: Deep reasoning workflows
    - tests/integration/: Focused component integration tests
"""
