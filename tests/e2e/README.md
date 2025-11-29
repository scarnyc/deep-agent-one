# End-to-End (E2E) Test Suite

## Overview

The E2E test suite validates complete user workflows and journeys through the Deep Agent One system with minimal mocking. These tests simulate real user interactions to verify that all components (API, services, agents, tools, database, external APIs) work together correctly.

## Purpose

E2E tests serve several critical purposes:

1. **Validate Complete Workflows**: Test entire user journeys from start to finish
2. **Integration Verification**: Ensure all components work together as a complete system
3. **User Experience Testing**: Verify real user scenarios and interactions
4. **Regression Prevention**: Catch breaking changes across component boundaries
5. **Performance Validation**: Measure end-to-end latency and throughput
6. **API Contract Testing**: Verify API responses match expectations

## Directory Structure

```
tests/e2e/
├── __init__.py                          # E2E test package documentation
├── README.md                            # This file
├── test_complete_workflows/             # Core workflow tests
│   ├── __init__.py                      # Workflow test documentation
│   ├── test_basic_chat.py              # Chat workflow (10 tests)
│   ├── test_hitl_workflow.py           # HITL approval workflow (12 tests)
│   └── test_tool_usage.py              # Tool execution workflow (14 tests)
├── test_user_journeys/                  # Multi-step user scenarios (Phase 1)
│   └── __init__.py                      # User journey documentation
└── test_reasoning_scenarios/            # Deep reasoning workflows (Phase 1)
    └── __init__.py                      # Reasoning scenario documentation
```

## Complete Workflows Tested

### 1. Basic Chat Workflow (`test_basic_chat.py`)

Tests the fundamental chat interaction flow with conversation history, input validation, and error handling.

**User Story**: As a user, I want to send messages and receive intelligent responses so that I can interact with the AI agent.

**Complete Flow**:
1. User sends chat message via API
2. FastAPI validates request
3. AgentService creates/retrieves agent
4. Agent processes message with GPT-5
5. Response returned to user
6. State persisted via checkpointer

**Tests** (10 total):
- `test_complete_chat_request_response_cycle`: Basic request/response flow
- `test_chat_workflow_with_conversation_history`: Multi-turn conversations
- `test_chat_workflow_validates_input`: Input validation (empty messages, invalid data)
- `test_chat_workflow_handles_long_messages`: Long message handling (2000+ chars)
- `test_chat_workflow_handles_unicode`: Unicode and emoji support
- `test_chat_workflow_with_metadata`: Request metadata processing
- `test_chat_workflow_error_recovery`: Error handling and recovery
- `test_chat_workflow_includes_request_id`: Request ID tracking
- `test_chat_workflow_concurrent_threads`: Thread safety and isolation
- `test_chat_response_time_under_threshold`: Performance validation (<2s)

**Success Criteria**:
- ✓ Response latency: <2s for simple queries
- ✓ Status code: 200 for valid requests, 422 for invalid
- ✓ Response structure: Valid `ChatResponse` model
- ✓ Thread isolation: No state leakage between threads
- ✓ Request tracking: X-Request-ID header present

### 2. Human-in-the-Loop (HITL) Workflow (`test_hitl_workflow.py`)

Tests the complete HITL approval flow including agent interruption, state persistence, and user approval/rejection.

**User Story**: As a user, I want to approve or reject risky agent actions so that I maintain control over the system.

**Complete Flow**:
1. Agent encounters action requiring approval
2. Agent enters interrupted state
3. State persisted via checkpointer
4. User checks agent status (shows "waiting for approval")
5. User sends approval/rejection/custom response
6. Agent resumes execution (if approved) or stops (if rejected)
7. Final response returned

**Tests** (12 total):

*Basic HITL*:
- `test_get_agent_status_shows_interrupted_state`: Status check during interruption
- `test_approve_hitl_action`: Approval allows continuation
- `test_reject_hitl_action`: Rejection stops execution
- `test_hitl_workflow_with_custom_response`: Custom user response

*Complex HITL*:
- `test_multiple_hitl_checkpoints_in_sequence`: Multiple approvals in one workflow
- `test_hitl_timeout_handling`: Long-waiting state handling

*Validation*:
- `test_approve_nonexistent_thread_returns_404`: Non-existent thread error
- `test_approve_invalid_action_returns_422`: Invalid action validation
- `test_approve_missing_required_fields_returns_422`: Required field validation

*State Persistence*:
- `test_hitl_state_persists_across_requests`: State consistency across checks

**Success Criteria**:
- ✓ HITL approval time: <30s (no automatic timeout)
- ✓ State persistence: Interrupted state maintained across requests
- ✓ Action types: approve, reject, respond (custom message)
- ✓ Error handling: 404 for missing threads, 422 for invalid actions

### 3. Tool Usage Workflow (`test_tool_usage.py`)

Tests the complete tool execution flow including file system tools and web search integration.

**User Story**: As a user, I want the agent to use tools (file operations, web search) to accomplish tasks so that it can interact with the environment.

**Complete Flow**:
1. User sends task requiring tools
2. Agent analyzes task and identifies needed tools
3. Agent invokes tools (file system, web search)
4. Tools execute and return results
5. Agent processes tool results
6. Agent responds with synthesized results
7. Tool calls logged via LangSmith

**Tests** (14 total):

*File System Tools*:
- `test_agent_uses_read_file_tool`: Read file contents
- `test_agent_uses_write_file_tool`: Create new files
- `test_agent_uses_ls_tool`: List directory contents
- `test_agent_uses_edit_file_tool`: Modify existing files

*Web Search Tool*:
- `test_agent_uses_web_search_tool`: Perplexity MCP web search

*Multiple Tools*:
- `test_agent_uses_multiple_tools_in_sequence`: Coordinated tool usage
- `test_agent_handles_tool_execution_errors`: Tool error handling

*Planning*:
- `test_agent_creates_plan_then_uses_tools`: TodoWrite planning + execution

*Transparency*:
- `test_tool_calls_are_logged`: Tool execution logging

*Performance*:
- `test_tool_execution_completes_within_threshold`: Tool latency (<2s)

**Success Criteria**:
- ✓ Tool execution: <2s for simple file operations
- ✓ Error handling: Graceful failures (file not found, etc.)
- ✓ Transparency: All tool calls logged via LangSmith
- ✓ Multiple tools: Correct execution order
- ✓ Planning: TodoWrite creates plans before execution

## Running E2E Tests

### Prerequisites

E2E tests require valid API keys and are designed for **Phase 0.5 Live API Integration Testing**. They are skipped in regular CI/CD runs.

**Required Environment Variables**:
```bash
# .env file
OPENAI_API_KEY=your_actual_openai_key  # Required for live testing
PERPLEXITY_API_KEY=your_perplexity_key # Required for web search tests
LANGCHAIN_API_KEY=your_langsmith_key   # Required for tracing tests
```

### Run All E2E Tests

```bash
# Run all E2E tests (requires valid API keys)
pytest tests/e2e/ -v --maxfail=1

# Run with detailed output
pytest tests/e2e/ -vv --tb=short

# Run specific workflow
pytest tests/e2e/test_complete_workflows/test_basic_chat.py -v
```

### Run by Test Category

```bash
# Basic chat workflow only
pytest tests/e2e/test_complete_workflows/test_basic_chat.py -v

# HITL workflow only
pytest tests/e2e/test_complete_workflows/test_hitl_workflow.py -v

# Tool usage workflow only
pytest tests/e2e/test_complete_workflows/test_tool_usage.py -v
```

### Run Specific Test

```bash
# Run single test by name
pytest tests/e2e/test_complete_workflows/test_basic_chat.py::TestBasicChatWorkflow::test_complete_chat_request_response_cycle -v
```

### Skip E2E Tests (Default in CI/CD)

E2E tests are automatically skipped when `OPENAI_API_KEY` is not set or starts with `your_`:

```python
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("your_"),
    reason="E2E tests require valid OPENAI_API_KEY (Phase 0.5 Live API Testing)"
)
```

## Writing E2E Tests

### Test Structure

E2E tests follow the **Arrange-Act-Assert (AAA)** pattern and are written as **user stories**:

```python
def test_complete_user_workflow(client: TestClient) -> None:
    """
    Test complete workflow from user perspective.

    User Story:
        As a user, I want to [action] so that [outcome].

    Flow:
        1. User performs action A
        2. System processes and responds
        3. User performs action B based on response
        4. System completes workflow

    Success Criteria:
        - Step A completes successfully
        - Response contains expected data
        - Step B executes correctly
        - Final state matches expectations
    """
    # Arrange (Given) - Set up test data
    request_data = {
        "message": "Test message",
        "thread_id": "test-thread-001",
    }

    # Act (When) - Execute the workflow
    response = client.post("/api/v1/chat", json=request_data)

    # Assert (Then) - Verify outcomes
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["thread_id"] == "test-thread-001"
```

### Best Practices

1. **User Story First**: Start with clear user story (As a..., I want..., so that...)
2. **Complete Flows**: Test entire workflows, not isolated components
3. **Realistic Data**: Use realistic test messages and scenarios
4. **Minimal Mocking**: Only mock external APIs (OpenAI, Perplexity, LangSmith)
5. **State Verification**: Verify state after each step
6. **Error Scenarios**: Test both happy paths and error cases
7. **Performance**: Keep tests fast (<30s per test)
8. **Independence**: Tests should not depend on each other
9. **Cleanup**: Use fixtures with teardown for resource cleanup
10. **Documentation**: Document user story, flow, and success criteria

### Fixture Guidelines

**Common Fixtures**:
```python
@pytest.fixture
def client() -> TestClient:
    """FastAPI test client (imports app locally to avoid circular deps)."""
    from backend.deep_agent.main import app
    return TestClient(app)

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for E2E tests (avoid actual API calls)."""
    with patch("langchain_openai.ChatOpenAI") as mock_client_class:
        # Mock setup
        yield mock_client

@pytest.fixture
def mock_langsmith():
    """Mock LangSmith tracing for E2E tests."""
    with patch("backend.deep_agent.integrations.langsmith.setup_langsmith"):
        yield

@pytest.fixture
def temp_workspace(tmp_path):
    """Temporary workspace for file tool tests."""
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir()
    yield workspace
```

### Test Naming Conventions

Use descriptive names that explain the complete workflow:

✅ **Good**:
- `test_complete_chat_request_response_cycle`
- `test_agent_uses_multiple_tools_in_sequence`
- `test_hitl_workflow_with_custom_response`

❌ **Bad**:
- `test_chat`
- `test_tools`
- `test_hitl`

### Assertions

Verify multiple aspects of each response:

```python
# Assert response structure
assert response.status_code == 200
assert "messages" in data
assert "thread_id" in data
assert "status" in data

# Assert response values
assert data["status"] == "success"
assert data["thread_id"] == expected_thread_id
assert len(data["messages"]) >= 1

# Assert business logic
chat_response = ChatResponse(**data)
assert chat_response.status == ResponseStatus.SUCCESS

# Assert performance
response_time = end_time - start_time
assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s threshold"
```

## Data Requirements

### Test Data Patterns

**Thread IDs**: Use descriptive, unique thread IDs:
```python
# Format: {test-type}-test-thread-{number}
thread_id = "basic-chat-test-thread-001"
thread_id = "hitl-test-thread-002"
thread_id = "tool-test-thread-003"
```

**Messages**: Use realistic, varied test messages:
```python
# Simple queries
"Hello, how can you help me?"
"What is the weather today?"

# Complex queries
"Analyze the impact of AI on software development and create a report"

# Tool-triggering queries
"List all files in the current directory"
"Search the web for latest Python news"

# Unicode/emoji
"Hello 世界! 🌍 How are you?"
```

**Metadata**: Include realistic metadata:
```python
metadata = {
    "user_id": "user-123",
    "source": "web",
    "session_id": "session-456",
}
```

### Data Cleanup

E2E tests should clean up resources after execution:

```python
@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace with automatic cleanup."""
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir()

    # Create test files
    (workspace / "test.txt").write_text("Test content")

    yield workspace

    # Cleanup happens automatically via tmp_path fixture
```

## Performance Expectations

E2E tests should meet the following performance targets:

### Response Time Targets (Phase 0)

| Workflow | Target | Test |
|----------|--------|------|
| Simple chat | <2s | `test_chat_response_time_under_threshold` |
| Tool execution | <2s | `test_tool_execution_completes_within_threshold` |
| HITL approval | <30s | User response time (no timeout) |
| Multi-step workflow | <10s | Phase 1 |
| Deep reasoning | <30s | Phase 1 |

### Test Execution Time

- **Individual test**: <30s per test
- **Complete workflow suite**: <10 minutes
- **All E2E tests**: <20 minutes

Slow tests indicate performance issues or excessive mocking setup.

## Dependencies

E2E tests depend on:

### Backend Components
- FastAPI application (`backend.deep_agent.main`)
- AgentService (`backend.deep_agent.services.agent_service`)
- LangGraph DeepAgents framework
- Checkpointer (state persistence)
- Tool implementations (file system, web search)

### External Services (Mocked)
- OpenAI GPT-5 API (via `langchain_openai.ChatOpenAI`)
- Perplexity MCP (web search)
- LangSmith (tracing)

### Test Infrastructure
- pytest test framework
- FastAPI TestClient
- unittest.mock for API mocking
- pytest fixtures for setup/teardown

## Related Documentation

- **[tests/e2e/__init__.py](tests/e2e/__init__.py)**: E2E test philosophy and overview
- **[tests/e2e/test_complete_workflows/__init__.py](tests/e2e/test_complete_workflows/__init__.py)**: Core workflow documentation
- **[tests/integration/README.md](tests/integration/README.md)**: Integration test guide
- **[tests/unit/README.md](tests/unit/README.md)**: Unit test guide
- **[CLAUDE.md](../../CLAUDE.md)**: Development guide and Phase 0 success criteria
- **[docs/development/testing.md](../../docs/development/testing.md)**: Comprehensive testing guide

## Troubleshooting

### Tests Skipped

**Problem**: All E2E tests skipped with "E2E tests require valid OPENAI_API_KEY"

**Solution**: Set valid API keys in `.env`:
```bash
OPENAI_API_KEY=your_actual_openai_key
# NOT: OPENAI_API_KEY=your_openai_api_key_here
```

### Import Errors

**Problem**: `ModuleNotFoundError` when running tests

**Solution**: Ensure virtual environment is activated and dependencies installed:
```bash
poetry shell
poetry install
```

### Timeout Errors

**Problem**: Tests timeout (>30s per test)

**Solution**: Check for:
- Excessive API calls (should be mocked)
- Missing mocks (causing real API calls)
- Infinite loops in agent logic

### State Leakage

**Problem**: Tests pass individually but fail when run together

**Solution**: Ensure test isolation:
- Use unique thread IDs per test
- Clean up resources in fixtures
- Don't share state between tests

## Future Enhancements (Phase 1+)

### Planned Test Categories

1. **User Journey Tests** (`test_user_journeys/`)
   - Multi-step research workflows
   - Code generation pipelines
   - Document creation and editing
   - Data analysis journeys

2. **Reasoning Scenario Tests** (`test_reasoning_scenarios/`)
   - Deep research with synthesis
   - Complex code generation with planning
   - Multi-constraint problem solving
   - Variable reasoning effort validation

3. **Performance Tests**
   - Load testing (concurrent users)
   - Stress testing (resource limits)
   - Endurance testing (long-running workflows)

4. **UI E2E Tests** (via Playwright MCP)
   - Frontend interaction testing
   - WebSocket streaming validation
   - AG-UI Protocol event testing

### Phase 1 Features to Test

- **Variable Reasoning Effort**: Test GPT-5 reasoning effort optimization
- **Memory System**: Test semantic search and context retrieval
- **Authentication**: Test OAuth 2.0 and token management
- **Provenance Store**: Test source tracking and citations
- **Enhanced AG-UI**: Test reasoning indicators and state events

## Contributing

When adding new E2E tests:

1. **Create user story** describing the workflow
2. **Write test** following AAA pattern
3. **Add docstring** with user story, flow, and success criteria
4. **Run test** to verify it passes
5. **Update documentation** (this README if new workflow)
6. **Commit** with semantic message: `test(e2e): add [workflow] E2E test`

Example commit:
```bash
git add tests/e2e/test_complete_workflows/test_new_workflow.py
git commit -m "test(e2e): add streaming chat workflow E2E test

- Test complete streaming chat flow with AG-UI Protocol events
- Verify TextMessageStart, TextMessageContent, TextMessageEnd
- Validate WebSocket connection handling
- 8 tests covering happy path, errors, disconnection

Tests: 8 tests, 100% pass, <30s execution time"
```

---

**Last Updated**: 2025-01-12
**Test Count**: 36 E2E tests (10 basic chat + 12 HITL + 14 tool usage)
**Coverage**: Core workflows (Phase 0 complete)
**Execution Time**: ~8 minutes for full E2E suite
