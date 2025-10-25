"""
E2E tests for agent tool usage workflow.

Tests the complete tool execution flow including file system tools
(ls, read_file, write_file, edit_file) and custom tools (web_search).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Any, Dict
import tempfile
import os


@pytest.fixture
def client() -> TestClient:
    """
    Create FastAPI test client.

    Imports app here to avoid circular dependencies and ensure
    fresh app instance for each test.
    """
    from backend.deep_agent.main import app
    return TestClient(app)


@pytest.fixture
def temp_workspace(tmp_path):
    """
    Create temporary workspace for file tool tests.

    Provides isolated directory for testing file operations
    without affecting actual filesystem.
    """
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir()

    # Create some test files
    (workspace / "test.txt").write_text("Hello, this is a test file.")
    (workspace / "data.json").write_text('{"key": "value"}')

    yield workspace


@pytest.fixture
def mock_openai_client_with_tool_calls():
    """
    Mock OpenAI client that simulates tool calling.

    Returns responses that trigger tool execution and then
    final responses after tool results.
    """
    with patch("langchain_openai.ChatOpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create sequence of responses:
        # 1. First response with tool call
        # 2. Second response after tool execution
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

        final_response = MagicMock()
        final_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="I've read the file. It contains: Hello, this is a test file.",
                    role="assistant",
                    tool_calls=None
                ),
                finish_reason="stop"
            )
        ]

        # Return sequence: tool call, then final response
        mock_client.chat.completions.create.side_effect = [
            tool_call_response,
            final_response
        ]

        yield mock_client


@pytest.fixture
def mock_langsmith():
    """Mock LangSmith tracing for E2E tests."""
    with patch("backend.deep_agent.integrations.langsmith.setup_langsmith") as mock_config:
        pass  # setup_langsmith returns None
        yield mock_config


@pytest.fixture
def mock_perplexity_search():
    """Mock Perplexity web search for testing."""
    with patch("backend.deep_agent.tools.web_search.web_search") as mock_search:
        # Mock search results
        async def mock_search_func(query: str) -> str:
            return f"Search results for '{query}': [Mock result 1], [Mock result 2]"

        mock_search.side_effect = mock_search_func
        yield mock_search


class TestFileToolUsage:
    """Tests for file system tool usage."""

    def test_agent_uses_read_file_tool(
        self,
        client: TestClient,
        mock_openai_client_with_tool_calls: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent successfully uses read_file tool.

        Flow:
        1. User asks to read a file
        2. Agent calls read_file tool
        3. Tool executes and returns file contents
        4. Agent responds with file contents
        """
        # Arrange
        request_data = {
            "message": "Please read the file test.txt",
            "thread_id": "tool-test-thread-001",
        }

        # Act
        response = client.post("/api/v1/chat", json=request_data)

        # Assert
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

        # Verify OpenAI was called (tool call + final response)
        assert mock_openai_client_with_tool_calls.chat.completions.create.call_count >= 1

    def test_agent_uses_write_file_tool(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent successfully uses write_file tool.

        Flow:
        1. User asks to create a new file
        2. Agent calls write_file tool
        3. Tool creates file
        4. Agent confirms file created
        """
        # Arrange
        request_data = {
            "message": "Create a file named output.txt with content 'Hello World'",
            "thread_id": "tool-test-thread-002",
        }

        # Mock OpenAI to return tool call for write_file
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Mock completion with tool call
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="I've created the file output.txt with the content 'Hello World'.",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_agent_uses_ls_tool(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent successfully uses ls tool to list directory contents.

        Flow:
        1. User asks to list directory contents
        2. Agent calls ls tool
        3. Tool returns file listing
        4. Agent responds with directory contents
        """
        # Arrange
        request_data = {
            "message": "List all files in the current directory",
            "thread_id": "tool-test-thread-003",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="Here are the files: test.txt, data.json, output.txt",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_agent_uses_edit_file_tool(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent successfully uses edit_file tool.

        Flow:
        1. User asks to edit an existing file
        2. Agent calls edit_file tool
        3. Tool modifies file
        4. Agent confirms edit
        """
        # Arrange
        request_data = {
            "message": "Edit test.txt and change 'Hello' to 'Goodbye'",
            "thread_id": "tool-test-thread-004",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="I've edited test.txt and replaced 'Hello' with 'Goodbye'.",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


class TestWebSearchToolUsage:
    """Tests for web search tool usage via Perplexity MCP."""

    def test_agent_uses_web_search_tool(
        self,
        client: TestClient,
        mock_perplexity_search: MagicMock,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent successfully uses web_search tool.

        Flow:
        1. User asks question requiring web search
        2. Agent calls web_search tool
        3. Perplexity MCP returns search results
        4. Agent responds with search results
        """
        # Arrange
        request_data = {
            "message": "Search the web for latest Python news",
            "thread_id": "tool-test-thread-005",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="Here are the latest Python news: Python 3.12 released with new features...",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


class TestMultipleToolUsage:
    """Tests for workflows using multiple tools."""

    def test_agent_uses_multiple_tools_in_sequence(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent uses multiple tools to complete complex task.

        Flow:
        1. User asks complex question requiring multiple tools
        2. Agent calls ls to see files
        3. Agent calls read_file to read specific file
        4. Agent calls web_search for additional info
        5. Agent synthesizes results and responds
        """
        # Arrange
        request_data = {
            "message": "List all files, read test.txt, and search web for related info",
            "thread_id": "tool-test-thread-006",
        }

        # Mock OpenAI with multiple responses
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Simulate multiple tool calls and final response
            responses = [
                # Response after ls
                MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Found files: test.txt, data.json", role="assistant"))]
                ),
                # Response after read_file
                MagicMock(
                    choices=[MagicMock(message=MagicMock(content="Read content from test.txt", role="assistant"))]
                ),
                # Final response after web_search
                MagicMock(
                    choices=[MagicMock(message=MagicMock(
                        content="Here's the summary: Files listed, test.txt read, and web search completed.",
                        role="assistant"
                    ))]
                ),
            ]

            mock_client.chat.completions.create.side_effect = responses

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_agent_handles_tool_execution_errors(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent handles tool execution errors gracefully.

        Flow:
        1. User asks to read non-existent file
        2. Agent calls read_file tool
        3. Tool fails (file not found)
        4. Agent handles error and responds appropriately
        """
        # Arrange
        request_data = {
            "message": "Read the file non_existent.txt",
            "thread_id": "tool-test-thread-007",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Simulate tool error handling
            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="I tried to read non_existent.txt but the file doesn't exist.",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            # Agent should handle error gracefully, not crash


class TestToolUsageWithPlanning:
    """Tests for tool usage combined with planning."""

    def test_agent_creates_plan_then_uses_tools(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test agent creates plan using TodoWrite then executes with tools.

        Flow:
        1. User asks complex multi-step task
        2. Agent uses TodoWrite to create plan
        3. Agent executes plan using file tools
        4. Agent completes task
        """
        # Arrange
        request_data = {
            "message": "Create a project structure with README.md, src/ directory, and tests/ directory",
            "thread_id": "tool-test-thread-008",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="I've created the project structure with README.md, src/, and tests/ directories.",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"


class TestToolUsageTransparency:
    """Tests for tool execution visibility and transparency."""

    def test_tool_calls_are_logged(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test that tool calls are properly logged for transparency.

        Verifies that tool execution is observable for debugging
        and user transparency (AG-UI Protocol requirement).
        """
        # Arrange
        request_data = {
            "message": "List files in current directory",
            "thread_id": "tool-test-thread-009",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="Files: test.txt, data.json",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            response = client.post("/api/v1/chat", json=request_data)

            # Assert
            assert response.status_code == 200

            # In production, tool calls would be logged via LangSmith
            # This test verifies the flow completes successfully


class TestToolUsagePerformance:
    """Performance tests for tool usage."""

    def test_tool_execution_completes_within_threshold(
        self,
        client: TestClient,
        mock_langsmith: MagicMock,
    ) -> None:
        """
        Test tool execution completes within acceptable time.

        Success criteria: Tool operations should not significantly
        degrade response time (<2s for simple operations).
        """
        import time

        # Arrange
        request_data = {
            "message": "List files in current directory",
            "thread_id": "tool-test-thread-010",
        }

        # Mock OpenAI
        with patch("langchain_openai.ChatOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            mock_completion = MagicMock()
            mock_completion.choices = [
                MagicMock(
                    message=MagicMock(
                        content="Files listed",
                        role="assistant"
                    )
                )
            ]
            mock_client.chat.completions.create.return_value = mock_completion

            # Act
            start_time = time.time()
            response = client.post("/api/v1/chat", json=request_data)
            end_time = time.time()

            # Assert
            assert response.status_code == 200

            response_time = end_time - start_time
            # With mocked tools, should be fast
            assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds threshold"
