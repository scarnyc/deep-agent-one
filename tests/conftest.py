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
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """
    Create temporary workspace for file operation tests.

    Provides isolated directory for testing file tools without
    affecting actual filesystem. Automatically cleaned up after test.

    Returns:
        Path to temporary workspace directory
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
    while avoiding actual API calls and charges.

    Yields:
        MagicMock of OpenAI client with pre-configured responses
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
    final responses after tool results.

    Yields:
        MagicMock configured for tool call scenarios
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
    the tracing code paths for integration testing.

    Yields:
        MagicMock of LangSmith config
    """
    with patch("backend.deep_agent.integrations.langsmith.get_langsmith_config") as mock_config:
        mock_config.return_value = None
        yield mock_config


@pytest.fixture
def mock_perplexity_search() -> Generator[AsyncMock, None, None]:
    """
    Mock Perplexity web search for testing.

    Provides fake search results without making actual API calls.

    Yields:
        AsyncMock of web_search function
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
    (invoke, get_state, update_state).

    Yields:
        AsyncMock of AgentService
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

    Returns:
        Dict with message and thread_id
    """
    return {
        "message": "Hello, agent! How are you?",
        "thread_id": "test-thread-123",
    }


@pytest.fixture
def sample_chat_response() -> dict:
    """
    Sample chat response for testing.

    Returns:
        Dict matching ChatResponse schema
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

    Returns:
        List of tool call dicts
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
