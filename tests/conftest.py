"""Pytest configuration and fixtures for Deep Agent AGI test suite."""
import pytest
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, AsyncMock, patch


# ============================================================================
# Directory Fixtures
# ============================================================================

@pytest.fixture
def project_root() -> Path:
    """
    Return the project root directory.

    Provides absolute path to the repository root for accessing
    project files during tests.

    Scope:
        Function-scoped (new instance per test)

    Returns:
        Path: Absolute path to project root directory

    Example:
        >>> def test_config_file(project_root):
        ...     config_file = project_root / "pyproject.toml"
        ...     assert config_file.exists()
    """
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """
    Return the test data directory.

    Provides path to the fixtures directory containing test data,
    mock responses, and shared test resources.

    Scope:
        Function-scoped (new instance per test)

    Dependencies:
        - project_root: Required to construct path

    Args:
        project_root: Path to project root directory

    Returns:
        Path: Absolute path to tests/fixtures directory

    Example:
        >>> def test_load_mock_data(test_data_dir):
        ...     mock_file = test_data_dir / "mock_responses" / "chat.json"
        ...     data = json.loads(mock_file.read_text())
    """
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """
    Create temporary workspace for file operation tests.

    Provides isolated directory for testing file tools without
    affecting actual filesystem. Automatically cleaned up after test.
    Pre-populated with sample files for common test scenarios.

    Scope:
        Function-scoped (fresh workspace per test)

    Dependencies:
        - tmp_path: pytest built-in fixture for temporary directories

    Args:
        tmp_path: pytest's temporary directory path

    Returns:
        Path: Temporary workspace directory with pre-created test files

    Pre-created Files:
        - test.txt: Plain text file
        - data.json: JSON file with sample data
        - config.yaml: YAML configuration file

    Lifecycle:
        Automatically cleaned up by pytest after test completion

    Example:
        >>> def test_read_file_tool(temp_workspace):
        ...     file_path = temp_workspace / "test.txt"
        ...     content = file_path.read_text()
        ...     assert "Hello" in content
    """
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir(exist_ok=True)

    # Create some test files
    (workspace / "test.txt").write_text("Hello, this is a test file.")
    (workspace / "data.json").write_text('{"key": "value", "count": 42}')
    (workspace / "config.yaml").write_text("setting: value\nenabled: true")

    return workspace


# ============================================================================
# Mock Service Fixtures (E2E Tests)
# ============================================================================

@pytest.fixture
def mock_openai_client() -> Generator[MagicMock, None, None]:
    """
    Mock OpenAI client for E2E tests.

    Mocks at the OpenAI client level to test complete internal flow
    while avoiding actual API calls and charges. Provides realistic
    chat completion responses with token usage tracking.

    Scope:
        Function-scoped (fresh mock per test)

    Dependencies:
        None (patches OpenAI at module level)

    Yields:
        MagicMock: OpenAI client with pre-configured chat.completions.create()

    Mock Behavior:
        - Returns single assistant message: "I'm a helpful AI assistant..."
        - Includes token usage metrics (10 prompt, 20 completion, 30 total)
        - finish_reason: "stop"
        - No tool calls

    Lifecycle:
        Context manager automatically cleans up patch after test

    Example:
        >>> def test_chat_endpoint(mock_openai_client):
        ...     # OpenAI client is already mocked
        ...     response = await agent_service.invoke("Hello")
        ...     assert "helpful AI assistant" in response["messages"][-1]["content"]
    """
    with patch("backend.deep_agent.services.llm_factory.OpenAI") as mock_client_class:
        # Create mock client instance
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock chat completion response
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(
                    content="I'm a helpful AI assistant. How can I assist you today?",
                    role="assistant",
                    tool_calls=None
                ),
                finish_reason="stop"
            )
        ]
        mock_completion.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )

        mock_client.chat.completions.create.return_value = mock_completion

        yield mock_client


@pytest.fixture
def mock_openai_client_with_tool_calls() -> Generator[MagicMock, None, None]:
    """
    Mock OpenAI client that simulates tool calling.

    Returns responses that trigger tool execution followed by
    final responses after tool results. Used for testing agent
    tool usage workflows.

    Scope:
        Function-scoped (fresh mock per test)

    Dependencies:
        None (patches OpenAI at module level)

    Yields:
        MagicMock: OpenAI client configured for multi-turn tool call flow

    Mock Behavior:
        - First call: Returns tool_calls (read_file with path="test.txt")
        - Second call: Returns final text response after tool execution
        - Simulates realistic LangGraph tool calling pattern

    Lifecycle:
        Context manager automatically cleans up patch after test

    Example:
        >>> def test_agent_with_tools(mock_openai_client_with_tool_calls, temp_workspace):
        ...     response = await agent_service.invoke("Read test.txt")
        ...     # Agent should have called read_file tool
        ...     assert "completed the task" in response["messages"][-1]["content"]
    """
    with patch("backend.deep_agent.services.llm_factory.OpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create sequence of responses:
        # 1. First response with tool call
        tool_call_response = MagicMock()
        tool_call_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=None,
                    role="assistant",
                    tool_calls=[
                        MagicMock(
                            id="call_123",
                            type="function",
                            function=MagicMock(
                                name="read_file",
                                arguments='{"path": "test.txt"}'
                            )
                        )
                    ]
                ),
                finish_reason="tool_calls"
            )
        ]

        # 2. Second response after tool execution
        final_response = MagicMock()
        final_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="I've completed the task using the tools.",
                    role="assistant",
                    tool_calls=None
                ),
                finish_reason="stop"
            )
        ]

        # Return sequence
        mock_client.chat.completions.create.side_effect = [
            tool_call_response,
            final_response
        ]

        yield mock_client


@pytest.fixture
def mock_langsmith() -> Generator[MagicMock, None, None]:
    """
    Mock LangSmith tracing for E2E tests.

    Prevents actual tracing calls during testing while maintaining
    the tracing code paths for integration testing. Returns None
    to disable tracing without breaking code that checks for config.

    Scope:
        Function-scoped (fresh mock per test)

    Dependencies:
        None (patches LangSmith at module level)

    Yields:
        MagicMock: LangSmith config getter that returns None (disabled)

    Mock Behavior:
        - get_langsmith_config() returns None (tracing disabled)
        - No actual traces sent to LangSmith API
        - Tracing code paths still executed for testing

    Lifecycle:
        Context manager automatically cleans up patch after test

    Example:
        >>> def test_agent_without_tracing(mock_langsmith):
        ...     # LangSmith is disabled but code still works
        ...     response = await agent_service.invoke("Hello")
        ...     assert response is not None
    """
    with patch("backend.deep_agent.integrations.langsmith.get_langsmith_config") as mock_config:
        mock_config.return_value = None
        yield mock_config


@pytest.fixture
def mock_perplexity_search() -> Generator[AsyncMock, None, None]:
    """
    Mock Perplexity web search for testing.

    Provides fake search results without making actual API calls
    to the Perplexity API. Returns consistent mock results for
    predictable testing.

    Scope:
        Function-scoped (fresh mock per test)

    Dependencies:
        None (patches web_search at module level)

    Yields:
        AsyncMock: web_search function that returns fake results

    Mock Behavior:
        - Returns: "Search results for '{query}': Mock result 1, Mock result 2, Mock result 3."
        - No actual network requests
        - Consistent results for reproducible tests

    Lifecycle:
        Context manager automatically cleans up patch after test

    Example:
        >>> @pytest.mark.asyncio
        ... async def test_web_search(mock_perplexity_search):
        ...     result = await web_search("Python docs")
        ...     assert "Mock result" in result
    """
    with patch("backend.deep_agent.tools.web_search.web_search") as mock_search:
        async def mock_search_func(query: str) -> str:
            return f"Search results for '{query}': Mock result 1, Mock result 2, Mock result 3."

        mock_search.side_effect = mock_search_func
        yield mock_search


@pytest.fixture
def mock_agent_service() -> Generator[AsyncMock, None, None]:
    """
    Mock AgentService for testing without actual agent execution.

    Provides pre-configured responses for common agent operations
    (invoke, get_state, update_state) without running actual LangGraph
    agent workflows. Useful for API endpoint testing.

    Scope:
        Function-scoped (fresh mock per test)

    Dependencies:
        None (patches AgentService at module level)

    Yields:
        AsyncMock: AgentService instance with mocked methods

    Mock Behavior:
        - invoke(): Returns mock conversation with user/assistant messages
        - get_state(): Returns mock state with empty next[] (completed)
        - update_state(): Returns None (no-op)

    Lifecycle:
        Context manager automatically cleans up patch after test

    Example:
        >>> @pytest.mark.asyncio
        ... async def test_chat_api(client, mock_agent_service):
        ...     response = await client.post("/api/v1/chat", json={"message": "Hello"})
        ...     assert response.status_code == 200
    """
    with patch("backend.deep_agent.api.v1.chat.AgentService") as mock_service_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_service_class.return_value = mock_instance

        # Mock successful invoke response
        mock_instance.invoke.return_value = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there! How can I help you?"},
            ]
        }

        # Mock get_state for HITL testing
        async def mock_get_state(**kwargs):
            return {
                "values": {"messages": []},
                "next": [],  # Empty = completed
                "config": {
                    "configurable": {
                        "thread_id": kwargs.get("thread_id", "test-thread"),
                        "checkpoint_id": "checkpoint-abc",
                    }
                },
                "metadata": {},
                "created_at": "2025-01-01T12:00:00",
                "parent_config": None,
            }

        mock_instance.get_state.side_effect = mock_get_state

        # Mock update_state for HITL approval
        mock_instance.update_state.return_value = None

        yield mock_instance


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_chat_message() -> dict:
    """
    Sample chat message for testing.

    Provides realistic chat message payload matching API schema.

    Scope:
        Function-scoped (new instance per test)

    Dependencies:
        None

    Returns:
        dict: Chat message with 'message' and 'thread_id' keys

    Schema:
        - message (str): User's message text
        - thread_id (str): Conversation thread identifier

    Example:
        >>> def test_chat_validation(sample_chat_message):
        ...     assert "message" in sample_chat_message
        ...     assert "thread_id" in sample_chat_message
    """
    return {
        "message": "Hello, agent! How are you?",
        "thread_id": "test-thread-123",
    }


@pytest.fixture
def sample_chat_response() -> dict:
    """
    Sample chat response for testing.

    Provides realistic chat response payload matching API schema.

    Scope:
        Function-scoped (new instance per test)

    Dependencies:
        None

    Returns:
        dict: Chat response with messages, thread_id, and status

    Schema:
        - messages (list): Conversation history [user, assistant messages]
        - thread_id (str): Conversation thread identifier
        - status (str): Response status ("success", "error", etc.)

    Example:
        >>> def test_response_validation(sample_chat_response):
        ...     assert sample_chat_response["status"] == "success"
        ...     assert len(sample_chat_response["messages"]) == 2
    """
    return {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! I'm doing well, thank you!"},
        ],
        "thread_id": "test-thread-123",
        "status": "success",
    }


@pytest.fixture
def sample_tool_calls() -> list:
    """
    Sample tool call data for testing.

    Provides realistic tool call payloads matching OpenAI's tool call format.
    Includes both arguments and results for complete testing scenarios.

    Scope:
        Function-scoped (new instance per test)

    Dependencies:
        None

    Returns:
        list: Tool calls with id, type, function details, and results

    Schema (per tool call):
        - id (str): Unique tool call identifier
        - type (str): Call type (usually "function")
        - function (dict):
            - name (str): Tool/function name
            - arguments (str): JSON-encoded arguments
        - result (str): Tool execution result (not in OpenAI schema, added for testing)

    Example:
        >>> def test_tool_parsing(sample_tool_calls):
        ...     assert len(sample_tool_calls) == 2
        ...     assert sample_tool_calls[0]["function"]["name"] == "read_file"
    """
    return [
        {
            "id": "call_001",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": '{"path": "test.txt"}',
            },
            "result": "File contents: Hello, world!",
        },
        {
            "id": "call_002",
            "type": "function",
            "function": {
                "name": "web_search",
                "arguments": '{"query": "Python documentation"}',
            },
            "result": "Search results: [Python.org, Real Python, ...]",
        },
    ]


# ============================================================================
# Async Test Support
# ============================================================================

@pytest.fixture
def event_loop():
    """
    Create event loop for async tests.

    Provides event loop for testing async functions and coroutines.
    Required for tests using @pytest.mark.asyncio.

    Scope:
        Function-scoped (fresh loop per test)

    Dependencies:
        None

    Yields:
        asyncio.AbstractEventLoop: New event loop instance

    Lifecycle:
        Automatically closed after test completion

    Example:
        >>> @pytest.mark.asyncio
        ... async def test_async_function(event_loop):
        ...     result = await some_async_function()
        ...     assert result is not None

    Note:
        pytest-asyncio provides this automatically, but explicit fixture
        ensures consistent behavior across different pytest versions.
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.

    Markers:
    - e2e: End-to-end tests (complete workflows)
    - unit: Unit tests (isolated components)
    - integration: Integration tests (component interactions)
    - slow: Slow tests (>5s execution time)
    - live_api: Live API integration tests (requires API keys, costs money)
    """
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests (>5s)")
    config.addinivalue_line("markers", "live_api: Live API tests (requires keys, costs money)")
